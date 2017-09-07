# -*- encoding: utf-8 -*-
import copy
import urllib
import urlparse

import msgpack
import simplejson as json

from common.utils import decider
from common.utils import time_utils
from common.utils import url_utils
from common.utils.managed_datastructures import ManagedHashMap
from common.utils.seo_utils import build_metric_tags
from config import locale as locale_config
from config.cache import KLP_FEED_CONN
from config.cache import KLP_FEED_EXPIRE_TIME_SECONDS
from config.cache import KLP_FEED_FORMAT
from config.cache import KLP_FEED_PREFIX
from config.cache import KLP_INTEREST_CONN
from config.cache import KLP_INTEREST_EXPIRE_TIME_SECONDS
from config.cache import KLP_INTEREST_FORMAT
from config.cache import KLP_INTEREST_PREFIX
from data_clients import terrapin_thrift_client
from data_clients.memcache import MemcacheClient
from data_clients.memcache import create_key_gen
from logger.statsd import opentsdb_client_v2
from logger.statsd import stat_client
from services.utils.barrier import BarrierAll
from settings import DEBUG
from settings import IS_EXTERNAL_DEV
from webapp import metatags
from webapp.resources import seo_utils
from webapp.resources import unauth_open_utils
from webapp.resources import unauth_utils
from webapp.resources.base_resource import APIStatus
from webapp.resources.base_resource import BaseResource
from webapp.resources.feed_resource import BaseFeedOfInterestsResource
from webapp.resources.feed_resource import BaseFeedOfPinsResource
from webapp.resources.node_resource_stub import NodeResourceStub
from webapp.resources.pin_resource import PinResource
from webapp.resources.related_interests_resource import RelatedInterestsResource
from webapp.utils import app_interstitial
from webapp.utils import metatag_keywords

INTEREST_FEED_RESOURCE_BATCH_EXPR = 'pin_join_manager_batch'
SEARCH_GUIDES_LIMIT = 25
AUTH_LP_PAGE_SIZE = 10

klp_feed_cache = MemcacheClient(
    KLP_FEED_CONN,
    create_key_gen(KLP_FEED_PREFIX, KLP_FEED_FORMAT, force_hash=True),
    KLP_FEED_EXPIRE_TIME_SECONDS)

interest_cache = MemcacheClient(
    KLP_INTEREST_CONN,
    create_key_gen(KLP_INTEREST_PREFIX, KLP_INTEREST_FORMAT, force_hash=True),
    KLP_INTEREST_EXPIRE_TIME_SECONDS)


class InterestResource(BaseResource):
    field_sets = {
        'default': (
            'interest.background_color',
            'interest.breadcrumbs',
            'interest.canonical_term',
            'interest.canonical_url',
            'interest.id',
            'interest.image_signature',
            'interest.image_size',
            'interest.image_source',
            'interest.images[474x, orig]',
            'interest.is_new',
            'interest.is_followed',
            'interest.is_interest',
            'interest.is_klp_term',
            'interest.key',
            'interest.name',
            'interest.type',
            'interest.url_name',
            'interest.has_related',
            'interest.klp_has_related',
            'interest.follower_count',
            'interest.feed_update_time',
            'interest.translation_urls',
        ),
        'unauth_react': (
            'interest.id',
            'interest.name',
            'interest.canonical_term',
            'interest.canonical_url',
            'interest.category',
            'interest.is_interest',
            'interest.is_klp_term',
            'interest.images[orig]',
            'interest.url_name',
            'interest.breadcrumbs',
            'interest.translation_urls',
            'interest.type',
        ),
        'auth_react_klp': PinResource.field_sets['react_grid_pin']
    }

    ja_enabled_editorial_klps = ManagedHashMap('seo',
                                               'editorial_klp_descriptions',
                                               'Japanese Editorial KLP Descriptions',
                                               'Descriptions for Enabled Japanese Editorial KLPs',
                                               use_config_backend=True)

    def _get_hreflang_data(self, data):
        """Return a dict used to render the appropriate hreflang meta tags on the page

        (1) If a term is translated for a given language, use that term and the interest ID in the URL
            e.g. /explore/桜-913796643374/
        (2) If the translation is missing or identical to the original term, use the original URL
            e.g. /explore/cherry-blossoms/
        -- update: 2015-09-01
        (3) The (1) and (2) failed to consider the i18n interest. i18n interest should also point to
        /explore/{term}-{id} to align with the URL.
        """
        hreflang_data = {}
        for locale, url in data.get('translation_urls').iteritems():
            hreflang_data[locale] = url

        if int(data.get('id')) == (data.get('canonical_term') or {}).get('id', 0):
            default_url = data.get('canonical_url')
        else:
            default_url = '/explore/%s/' % data.get('url_name')

        for locale in locale_config.LOCALE_TO_SUBDOMAIN.keys():
            if locale not in hreflang_data:
                hreflang_data[locale] = default_url
        hreflang_data['en-US'] = default_url
        return hreflang_data

    def _get_cache_settings(self):
        # If false, the cache will also not be updated, even if a cache experiment is set to invalidate.
        # In general, it will be set to 100.
        klp_cache_decider = decider.decide_experiment('klp_interest_cache')

        # For unauth and 'no_gift_wrap=true' we won't show gift wrap. This is necessary for KLP Pipeline
        # when we use human eval for feed relevance. Don't use the cache in this case.
        test_user = not self.context.is_authenticated and \
            (self.options.get('no_gift_wrap') == 'true' or
             (self.context.request_debug and self.context.request_debug.get('deb_d')))

        # This decider exists so that we can quickly update the cache when we make a large change to the related KLPs.
        # In general, it should be set to 0.
        klp_cache_invalidate_decider = decider.decide_experiment('klp_interest_cache_invalidate')

        interest_cache_exp_group = self.context.experiments.v2_activate_experiment('interest_cache')
        cache_manager_exp_group = self.context.experiments.v2_activate_experiment('unauth_cache_manager')

        # Don't fetch from cache, but update the cache with the newly generated result.
        invalidate_cache = (
            klp_cache_invalidate_decider or
            interest_cache_exp_group == 'invalidate' or
            cache_manager_exp_group == 'invalidate'
        )

        # Don't fetch from cache and don't update the cache.
        # Note that disable overrides invalidate.
        disable_cache = (
            interest_cache_exp_group == 'disabled' or
            cache_manager_exp_group == 'disabled' or
            test_user
        )

        fetch_from_cache = (
            klp_cache_decider and
            not invalidate_cache and
            not disable_cache
        )

        update_cache = (
            klp_cache_decider and
            not disable_cache
        )

        return fetch_from_cache, update_cache

    def _get_cache_key(self, interest, field_set_key):
        return interest, self.context.locale.lower(), field_set_key

    def _get_cached_response(self, cache_key):
        cached_result = interest_cache.get(cache_key)
        return msgpack.unpackb(cached_result, encoding="utf-8") if cached_result else None

    def _in_pure_react_exp(self):
        pure_react_group = self.context.experiments.v2_activate_experiment('web_pure_react2') or ''
        return ('enabled' in pure_react_group or 'employees' in pure_react_group)

    def _auth_klp_refresh_experiment_gating(self):
        main_module_name = self.options.get('main_module_name')
        if (self.context.is_authenticated and main_module_name == 'InterestFeedPage'):
            return 'enabled_react_klp'

    def _auth_klp_format_data(self, response):
        formatted_data = {}
        formatted_data['query'] = response.get('query', '')
        formatted_data['guides'] = response.get('terms', [])
        formatted_data['results'] = response.get('data', [])
        formatted_data['is_auth_klp'] = True
        response['data'] = formatted_data

    def get(self):
        start_time_ms = time_utils.now_millis()
        if self.options['interest'] is not None:
            self.options['interest'] = self.options['interest'].lower()
        interest_id = url_utils.parse_interest_id(self.options['interest'])
        interest = interest_id if interest_id else self.options['interest']
        field_set_key = self.get_field_set_key()
        resp = None
        fetch_from_cache, update_cache = self._get_cache_settings()
        cache_key = self._get_cache_key(interest, field_set_key)
        is_debug_mode = False
        if self.context.request_debug and self.context.request_debug.get('deb_d'):
            is_debug_mode = True

        if fetch_from_cache:
            resp = self._get_cached_response(cache_key)

        if resp:
            data = resp.get('data')
        else:
            klp_start_time_ms = time_utils.now_millis()
            resp = self.request('/v3/klp/%s/' % interest, field_set_key=field_set_key)
            if resp.get('status') != APIStatus.SUCCESS:
                return resp
            klp_end_start_time_ms = time_utils.now_millis()

            opentsdb_client_v2.timing('denzel.resource.InterestResource.api.klp',
                                      klp_end_start_time_ms - klp_start_time_ms, sample_rate=1,
                                      tags=build_metric_tags(self.context))

            data = resp.get('data')

            # Use entire interest query to extract KLP if id is not a valid KLP id
            if interest_id and data and data['id'] == '0':
                interest = self.options['interest']
                origin_resp = self.request('/v3/klp/%s/' % interest,
                                           field_set_key=field_set_key,
                                           ignore_bookmark=True)
                if origin_resp.get('status') != APIStatus.SUCCESS:
                    return origin_resp
                data = origin_resp.get('data')

            if self.context.is_mobile_agent and field_set_key != 'unauth_react':
                self.context.app_interstitial_data = app_interstitial.get_interest_data(data)

            # All the logic below that sets page-level redirects and meta tags should only execute
            # on /explore/ pages (if InterestResource is the main module's resource)
            # TODO (jean): Work with Web team on a better solution. This problem affects other resources too.
            if not self.context.visible_url.startswith('/explore/'):
                return resp

            # This could happen if the interest is a banned term
            if not data:
                resp['data'] = {'name': self.options['interest'].replace('-', ' ')}
                return resp

            canonical_term_id = (data.get('canonical_term') or {}).get('id', 0)

            # Set and 301 redirect to the canonical URL as appropriate.
            # (1) For terms with translations, the canonical URL for a locale (or subdomain)
            #     will contain the translation for that locale.
            #     Examples: /explore/asia-travel/ => /explore/asienreisen-924772690748/ for de
            #               /explore/asia-travel/ => explore/アジア旅行-924772690748/ for ja
            # (2) Some terms canonicalize to other terms because they are duplicates,
            #     such as mis-spellings or abbreviations.
            #     In this case, we do not change the behavior for auth interests,
            #     since the user may be following the interest.
            #     Examples: /explore/httyd/ => /explore/how-to-train-your-dragon/ (interest, unauth only)
            #               /explore/10th-doctor/ => /explore/tenth-doctor/ (interest, unauth only)
            #               /explore/1-direction-cakes/ => /explore/one-direction-cakes/ (not interest, auth + unauth)
            #               /explore/amish-bread/ => /explore/amish-bread-recipes/ (not interest, auth + unauth)
            if (canonical_term_id and
                # Non-English canonical interests have canonical_term_id = id
                # Example: /explore/大福/ (no redirect)
                    data.get('id') and canonical_term_id != int(data.get('id')) and
                # Do not change interest URLs for auth users
                    (not data.get('is_interest') or not self.context.is_authenticated)):
                        canonical_resp = self.request('/v3/klp/%s/' % canonical_term_id,
                                                      field_set_key=field_set_key,
                                                      ignore_bookmark=True)
                        data = canonical_resp.get('data') or {}
                        resp['data'] = data

            if is_debug_mode:
                resp['data']['is_debug_mode'] = True

            # only cache results for terms in the dictionary
            is_dictionary_term = data.get('id') and data.get('id') != '0'
            if update_cache and is_dictionary_term:
                interest_cache.set(cache_key, msgpack.packb(resp, use_bin_type=True, encoding="utf-8"))

        # For unauth and 'no_gift_wrap=true' we won't show gift wrap. This is necessary for KLP Pipeline
        # when we use human eval for feed relevance.
        if not self.context.is_authenticated and (self.options.get('no_gift_wrap') == 'true' or is_debug_mode):
            resp['data']['no_gift_wrap'] = True
        else:
            resp['data']['no_gift_wrap'] = False

        redirect_url = determine_explore_redirect(data, self.options.get('interest'), self.context)
        if redirect_url:
            # This response is specific to pure react explore pages
            if self.options.get('pure_react'):
                resp['data'] = {
                    'redirect_url': redirect_url
                }
            else:
                self.context.redirect = redirect_url
            return resp

        if not data.get('is_klp_term'):
            resp['data'] = {
                'id': '0',
                'name': data.get('name', ''),
                'is_interest': data.get('is_interest', False),
                'is_klp_term': data.get('is_klp_term', False),
            }
            stat_client.increment('seo.klp.non_klp_term', sample_rate=1)
            return resp

        end_time_ms = time_utils.now_millis()
        opentsdb_client_v2.timing('denzel.resource.InterestResource.get',
                                  end_time_ms - start_time_ms, sample_rate=0.05,
                                  tags=build_metric_tags(self.context))

        name = data.get('name')
        if self.ja_enabled_editorial_klps.contains(name):
            resp['data']['description'] = self.ja_enabled_editorial_klps.get(name)

        auth_klp_group = self._auth_klp_refresh_experiment_gating()
        if auth_klp_group == 'enabled_react_klp' or self._in_pure_react_exp():
            self.options['bookmarks'] = []
            # If a canonical interest was found we should use that instead of the original interest
            interest = resp.get('data', {}).get('name', None) or interest
            data = {
                'allow_horizontal_guides': True,
                'guides_size': SEARCH_GUIDES_LIMIT,
                'interest': interest,
                'page_size': AUTH_LP_PAGE_SIZE
            }
            response = self.request('/v3/auth-landing-page/pins/', data=data, field_set_key='auth_react_klp')
            if response.get('status') == APIStatus.SUCCESS and response.get('data'):
                self._auth_klp_format_data(response)
                return response
            else:
                stat_client.increment('interests_resource.auth_react_klp.api_error')

        return resp

    def _get_interest_for_metadata(self, interest, field_set_key):
        response = None
        cache_hit = True
        start_time_ms = time_utils.now_millis()
        fetch_from_cache, _ = self._get_cache_settings()
        if fetch_from_cache:
            response = self._get_cached_response(self._get_cache_key(interest, field_set_key))

        if response is None:
            cache_hit = False
            response = self.request(
                '/v3/klp/%s/' % interest,
                data={'fields': 'interest.name,interest.images[orig],interest.is_klp_term,interest.is_interest,' +
                                'interest.id,interest.translation_urls,interest.url_name,interest.canonical_term,' +
                                'interest.canonical_url'},
                ignore_bookmark=True)

        end_time_ms = time_utils.now_millis()
        opentsdb_client_v2.timing('denzel.resource.InterestResource.get_page_metadata.api',
                                  end_time_ms - start_time_ms, sample_rate=0.05,
                                  tags=build_metric_tags(self.context, {'cached': str(cache_hit)}))
        return response

    def get_page_metadata(self):
        start_time_ms = time_utils.now_millis()
        interest_id = url_utils.parse_interest_id(self.options['interest'])
        interest = interest_id if interest_id else self.options['interest']
        field_set_key = self.get_field_set_key()

        # Temporary fix for /explore/explore page until api would get rid of the v3/interests/explore/ endpoint.
        # TODO (vadim): follow up with Yan Sun after 9/30/15 if android still have a dependency on it.
        if interest == 'explore':
            return {'robots': 'noindex'}

        response = self._get_interest_for_metadata(interest, field_set_key)

        if response.get('status') == APIStatus.SUCCESS:
            interest_data = response.get('data') or {}

            canonical_term_id = (interest_data.get('canonical_term') or {}).get('id', 0)
            if canonical_term_id and canonical_term_id != int(interest_data.get('id')):
                response = self._get_interest_for_metadata(str(canonical_term_id), field_set_key)
                if response.get('status') == APIStatus.SUCCESS:
                    interest_data = response.get('data', {})

            # This could happen if the interest is a banned term
            if not interest_data:
                return {'robots': 'noindex'}

            if not self.context.is_authenticated:
                related_klps = metatag_keywords.get_related_keywords(self, interest_id=interest_data.get('id'))
                interest_data['related_klps'] = related_klps.get('data', {})
            metadata = metatags.get_interest_metadata(self.context, interest_data)

            # We don't want non-dictionary terms to be indexed, even if we need
            # to continue to support certain pages that have already been
            # linked to in hashtag descriptions and followed by users
            # NOTE: this was originally is_seo, but we changed it when we
            # we removed "seo" from our client-visable source
            if not interest_data.get('is_klp_term'):
                metadata['robots'] = 'noindex'

            metatags.log_page_title(self, metatags.PAGE_TYPE_INTEREST, metadata['title'], self.context['full_path'])

            metadata['hreflang_data'] = self._get_hreflang_data(interest_data)
            if self.context.is_bot == 'true':
                amp_klp_group = self.context.activate_seo_or_unauth_experiment('amp_klp')
            else:
                amp_klp_group = self.context.get_seo_experiment_group('seo_amp_klp')
            if not self.context['is_amp'] and amp_klp_group and amp_klp_group.startswith('enabled'):
                metadata['links'] = \
                    [('amphtml', self.context.get_canonical_absolute_url().replace('/explore/', '/amp/explore/', 1))]

            end_time_ms = time_utils.now_millis()
            opentsdb_client_v2.timing('denzel.resource.InterestResource.get_page_metadata',
                                      end_time_ms - start_time_ms, sample_rate=0.1,
                                      tags=build_metric_tags(self.context))
            return metadata


def determine_explore_redirect(data, interest, context):
    """
    Encapsulates redirect logic associated with the unauth KLP page.
        `data` expects the following shape: { 'canonical_url', 'id' }
    """
    if int(data.get('id', 0)) and data.get('canonical_url') and context.is_full_page:
        context['canonical_url'] = data.get('canonical_url')
        if context['canonical_url'] != '/explore/%s/' % interest.replace(' ', '-'):
            options = []
            redirect_url = context['canonical_url']
            if context.is_amp:
                redirect_url = '/amp' + redirect_url

            parsed_url = urlparse.urlparse(context['full_path'])
            if parsed_url.query:
                for param, value in urlparse.parse_qsl(parsed_url.query):
                    if param == 'nogw' or param.startswith('exp_'):
                        options.append(param + "=" + value)

            # Redirect 301 for bots and 302 for users
            context.temporary_redirect = context.is_bot != 'true'

            stat_client.increment('seo.klp.redirect.canonical', sample_rate=1)

            if options:
                return "%s?%s" % (redirect_url, "&".join(options))
            else:
                return redirect_url

    if context.is_authenticated and not data.get('is_klp_term'):
        return "/search/pins/?q=%s" % interest


class TopicResource(BaseResource):
    field_sets = {
        'default': (
            'interest.background_color',
            'interest.canonical_term',
            'interest.canonical_url',
            'interest.id',
            'interest.image_signature',
            'interest.image_size',
            'interest.image_source',
            'interest.images[474x, orig]',
            'interest.is_new',
            'interest.is_followed',
            'interest.is_interest',
            'interest.is_klp_term',
            'interest.key',
            'interest.name',
            'interest.type',
            'interest.url_name',
            'interest.has_related',
            'interest.klp_has_related',
            'interest.follower_count',
            'interest.feed_update_time',
        )
    }

    def get(self):
        if self.options['interest'] is not None:
            self.options['interest'] = self.options['interest'].lower()
        interest_id = url_utils.parse_interest_id(self.options['interest'])
        interest = interest_id if interest_id else self.options['interest']

        # Temporary fix for /explore/explore page until api would get rid of the v3/interests/explore/ endpoint.
        # TODO (vadim): follow up with Yan Sun after 9/30/15 if android still have a dependency on it.
        if interest == 'explore':
            resp = {}
            resp['data'] = {'name': self.options['interest'].replace('-', ' ')}
            return resp

        field_set = 'default'

        resp = self.request('/v3/interests/%s/' % interest, field_set_key=field_set)
        if resp.get('status') != APIStatus.SUCCESS:
            return resp

        data = resp.get('data')
        if self.context.is_mobile_agent:
            self.context.app_interstitial_data = app_interstitial.get_interest_data(data)

        return resp


SEARCH_BOOST_COUNTRIES = frozenset('US, FR, GB')


class BaseInterestsFeedResource(BaseResource):

    default_field_set_key = 'pins'
    field_sets = {
        'pins': BaseFeedOfPinsResource.field_sets['interest_grid_item'],
        'unauth_react': PinResource.field_sets['unauth_react_grid_item'],
    }

    def get_field_set(self):
        """Override"""
        fields = super(BaseInterestsFeedResource, self).get_field_set()
        field_set_key = self.get_field_set_key()

        if field_set_key == 'pins':
            fields += PinResource.experiments_additional_field_sets['did_it']

        return fields

    def _get_visual_data(self, data):
        start_time_ms = time_utils.now_millis()
        result = seo_utils.add_visual_data(self, data)
        opentsdb_client_v2.timing('denzel.resource.InterestsFeedResource.visualdata.get',
                                  time_utils.now_millis() - start_time_ms, sample_rate=1,
                                  tags=build_metric_tags(self.context))
        return result

    def _filter_duplicate_images(self, data):
        filtered_data = []
        images = set()
        for pin in data:
            if pin and pin.get('image_signature') and pin.get('image_signature') not in images:
                images.add(pin.get('image_signature'))
                filtered_data.append(pin)
        return filtered_data

    def _augment_result_data(self, result):
        data = self._filter_duplicate_images(result.get('data'))
        if self.options.get('add_vase') and self.context.language in seo_utils.VISUAL_DESCRIPTION_LANGUAGES:
            self._get_visual_data(data)
        # Add information for board backlink experiment.
        # TODO(cmiranda): Remove when experiment is over.
        seo_utils.add_board_backlinks_data(self, data)

    def _add_base64_encodings(self, result, base64_pins_count):
        img_sigs = [pin['image_signature'] for pin in result['data']['results'][0: base64_pins_count]]
        base64_url = "/v3/images/base64/"
        encodings_start_time = time_utils.now_millis()
        encodings = self.request(base64_url, ignore_bookmark=True, data={'img_sigs': ','.join(img_sigs)})
        encodings_end_time = time_utils.now_millis()
        opentsdb_client_v2.timing('denzel.resource.base64.request',
                                  encodings_end_time - encodings_start_time, sample_rate=1,
                                  tags=build_metric_tags(self.context))
        if encodings.get('data') and encodings.get('status') == APIStatus.SUCCESS:
            for pin in result['data']['results']:
                image_encoding = encodings['data'].get(pin['image_signature'])
                if image_encoding:
                    pin['base64'] = encodings['data'][pin['image_signature']]
        return result

    def _repackage_data(self, result):
        # discovery_debug expects a certain object structure, repackage
        newData = {}
        newData['results'] = result.get('data')

        if result.get('debug_data'):
            newData['debug'] = result.get('debug_data')
        return newData

    def _get_base64_number_images(self, received_combined_bookmark):
        # we only want base64 on first page.  If we received a bookmark we are on subsequent page
        if received_combined_bookmark is not None:
            return None
        base64_group = self.context.experiments.v2_activate_experiment('base64_pin_images_klp')
        if not base64_group or 'enabled_' not in base64_group:
            return None
        else:
            num_base64 = base64_group.split('_')[1]
            if num_base64.isdigit():
                return int(num_base64)
            else:
                self.response_error('_get_base64_number_images base64_group is unclear')

    def _get_cache_settings(self):
        klp_feed_cache_decider = decider.decide_experiment('klp_feed_cache')
        klp_feed_cache_invalidate_decider = decider.decide_experiment('klp_feed_cache_invalidate')

        klp_cache_exp_group = self.context.experiments.v2_activate_experiment('klp_cache')
        cache_manager_exp_group = self.context.experiments.v2_activate_experiment('unauth_cache_manager')

        # Don't fetch from cache, but update the cache with the newly generated result.
        invalidate_cache = (
            klp_feed_cache_invalidate_decider or
            klp_cache_exp_group == 'invalidate' or
            cache_manager_exp_group == 'invalidate'
        )

        # Don't fetch from cache and don't update the cache.
        # Note that disable overrides invalidate.
        disable_cache = (
            klp_cache_exp_group == 'disabled' or
            cache_manager_exp_group == 'disabled'
        )

        fetch_from_cache = (
            klp_feed_cache_decider and
            not invalidate_cache and
            not disable_cache
        )

        update_cache = (
            klp_feed_cache_decider and
            not disable_cache
        )

        # Experiment to test the value of caching.
        if fetch_from_cache and self.context.experiments.v2_activate_experiment('unauth_klp_cache') == 'no_cache':
            fetch_from_cache = False
            update_cache = False

        return fetch_from_cache, update_cache

    def _get_klp_api_feed_generator(self, interest_key, cache_page_size, field_set_key):
        def _get_klp_api_feed(api_bookmark):
            api_input_data = {}
            if self.context.request_debug:
                api_input_data.update(self.context.request_debug)
            api_input_data.update({'page_size': cache_page_size})
            api_input_data.update({'bookmark': api_bookmark})
            kwargs = {'data': api_input_data}
            kwargs['field_set_key'] = field_set_key
            klp_feed_url = "/v3/klp/%s/feed/"
            result = self.request(klp_feed_url % interest_key, **kwargs)
            if result and result.get('data') and result.get('status') == APIStatus.SUCCESS:
                self._augment_result_data(result)
                result['data'] = unauth_utils.canonicalize_pin_ids(result.get('data'), self.context.language)
            return result
        return _get_klp_api_feed

    def _get_cached_klp_feed(self, interest_id, interest_key, client_page_size):
        start_time_ms = time_utils.now_millis()
        experiments = ':devapp:%d' % (DEBUG or IS_EXTERNAL_DEV) if (DEBUG or IS_EXTERNAL_DEV) else ''

        # Use running experiments from ngapi. Should be in sync with core/logic/seo_logic.py
        # The loop does nothing when there're no active experiments.
        # It's kept here to make sure it would be used for all new experiments.
        for seo_experiment in ('unauth_ranking_vase_2', 'unauth_ranking_jp', 'unauth_ranking_tres'):
            if seo_experiment == 'unauth_ranking_jp' and self.context.country != 'JP':
                continue
            if seo_experiment == 'unauth_ranking_tres' and self.context.country not in ('ES', 'MX', 'AR'):
                continue
            group = self.context.activate_seo_or_unauth_experiment(seo_experiment)

            # Do not use control in the cache key
            if group and not group.startswith('control'):
                experiments += ':%s=%s' % (seo_experiment, group)

        field_set_key = self.get_field_set_key()
        vase_key = self.options.get('add_vase') and self.context.language in seo_utils.VISUAL_DESCRIPTION_LANGUAGES
        combined_bookmark = self.get_latest_bookmark()
        received_combined_bookmark = combined_bookmark
        if interest_id:
            fetch_from_cache, update_cache = self._get_cache_settings()
        else:
            fetch_from_cache = False
            update_cache = False
        cache_page_size = 25
        use_compression = True

        # klp_cache_key_salt added to cache key in unauth_utils, invalidates cache and replace with new cache values
        klp_cache_key_salt = decider.decide_experiment('klp_cache_key_salt')

        cache_key_static_params = str(interest_id) + str(1 if vase_key else 0) + str(self.context.locale.lower()) + \
            str(field_set_key) + str(experiments)

        klp_api_feed_generator = self._get_klp_api_feed_generator(interest_key, cache_page_size, field_set_key)

        result, combined_bookmark, cache_hit = unauth_utils.get_cached_feed(combined_bookmark, cache_page_size,
                                                                            client_page_size, fetch_from_cache,
                                                                            update_cache,
                                                                            cache_key_static_params,
                                                                            klp_api_feed_generator, klp_feed_cache,
                                                                            use_compression, klp_cache_key_salt)

        self.add_bookmark(combined_bookmark)

        # data augmentation
        if result.get('data'):
            if self.context.is_full_page:
                seo_utils.holdout_leaf_snippet(self, result['data'], ('holdout_klp', 'holdout_klp_2'))

        # repackage
        result['data'] = self._repackage_data(result)

        if result.get('status') == APIStatus.SUCCESS:
            opentsdb_client_v2.timing('denzel.resource.InterestsFeedResource.get',
                                      time_utils.now_millis() - start_time_ms, sample_rate=0.05,
                                      tags=build_metric_tags(self.context, {'cached': str(cache_hit)}))
            base64_pins_count = self._get_base64_number_images(received_combined_bookmark)
            if base64_pins_count and result['data']:
                result = self._add_base64_encodings(result, base64_pins_count)
        return result

    def get(self):
        opentsdb_client_v2.increment('denzel.resource.BaseInterestsFeedResource.get', sample_rate=0.1,
                                     tags=build_metric_tags(self.context))

        interest = self.options.get("interest")
        if not interest:
            return self.response_error("Empty interest field")

        interest_name = self.options.get('interest_name', '')

        interest_id = url_utils.parse_interest_id(interest)
        # pass a key derived from interest name when interest_id is missing (for non-dictionary terms)
        # if interest name is blank, pass '0' (the string), so the klp API call succeeds
        interest_key = (interest_id or
                        interest_name.lower().replace(' ', '-') or
                        '0')
        default_page_size = 125 if (self.context.is_bot == 'true') else 25
        page_size = self.options.get('page_size', default_page_size)

        # We return empty results for crawlers here to save search capacity because these "fake" KLPs are no-indexed
        if not interest_id and not self.context.is_authenticated and self.context.is_bot == 'true':
            return {'data': {'results': []}}
        # We are getting spam requests directly to the resource where page_size is none.
        # In these cases we should pass back empty result
        if not page_size:
            return {'data': {'results': []}}
        else:
            return self._get_cached_klp_feed(interest_id, interest_key, page_size)


class InterestsFeedResource(BaseInterestsFeedResource):
    def get(self):
        response = super(InterestsFeedResource, self).get()
        response_copy = copy.copy(response)
        data = response_copy.get('data')
        if data:
            response_copy['data'] = data.get('results')
        return response_copy


class TopicFeedResource(BaseResource):
    default_field_set_key = 'pins'
    field_sets = {
        'pins': BaseFeedOfPinsResource.field_sets['interest_grid_item'],
        'unauth_react': PinResource.field_sets['unauth_react_grid_item']
    }

    _RELATED_BOARDS_MODULE_NUMBER_BOARDS = 5

    def get_field_set(self):
        """Override"""
        fields = super(TopicFeedResource, self).get_field_set()
        field_set_key = self.get_field_set_key()

        if field_set_key == 'pins':
            fields += PinResource.experiments_additional_field_sets['did_it']

        return fields

    def get(self):
        start_time_ms = time_utils.now_millis()
        interest = self.options.get("interest")
        if not interest:
            return self.response_error("Empty interest field")

        debug_data = {}
        debug_on = False
        feed_type = self.options.get("feed_type", 'prod')
        if self.context.request_debug:
            debug_on = True if self.context.request_debug.get('deb_d') == "True" else False
            feed_type = self.context.request_debug.get('deb_feed')
            debug_data['deb_limit'] = self.context.request_debug.get('deb_limit')
            debug_data['generator'] = self.context.request_debug.get('deb_generator')
            debug_data['enable_scorer'] = False \
                if self.context.request_debug.get('deb_scorer') == "False" else True
            debug_data['deb_exp_segment'] = True \
                if self.context.request_debug.get('deb_exp_segment') == "True" else False
        response = self.request("/v3/interests/%s/feed/" % interest,
                                data={'feed_type': feed_type, 'debug_on': debug_on,
                                      'debug_options': json.dumps(debug_data)})
        if response.get('status') != APIStatus.SUCCESS:
            return response

        end_time_ms = time_utils.now_millis()
        opentsdb_client_v2.timing('denzel.resource.TopicFeedResource.get',
                                  end_time_ms - start_time_ms, sample_rate=1,
                                  tags=build_metric_tags(self.context))
        return response


class UserInterestsResource(BaseResource):
    default_field_set_key = 'grid_item'
    field_sets = {
        'grid_item': BaseFeedOfInterestsResource.field_sets['grid_item'],
        # For internal/interests use only
        'grid_item_internal': tuple(list(BaseFeedOfInterestsResource.field_sets['grid_item']) +
                                    ['interest.recommendation_source']),
        'grid_item_nux': tuple(list(
            BaseFeedOfInterestsResource.field_sets['grid_item']) + ['interest.is_recommended', 'interest.log_data']),
        'related_interest': (
            'interest.name',
            # 'interest.has_related', waiting on API support
            'interest.id',
            'interest.type',
            'interest.url_name'
        ),

    }


class UrlInterestsResource(BaseResource):
    default_field_set_key = 'grid_item'
    field_sets = {
        'grid_item': BaseFeedOfInterestsResource.field_sets['grid_item'],
    }

    def get(self):
        url = self.options.get('url', 'http://www.google.com')
        sort = self.options.get('sort', True)
        return self.request('/vx/links/interests/', data={'link': url, 'sort': sort})


class KLPBarResource(BaseResource):
    default_field_set_key = 'annotations'
    field_sets = {
        'annotations': (
            'interest.id',
            'interest.is_interest',
            'interest.is_klp_term',
            'interest.name',
            'interest.key',
            'interest.url_name'
        ),
    }
    KEYWORD_LIMIT = 8

    def _get_interest_info(self, interest_name):
        response = self.request(
            '/v3/klp/%s/' % interest_name,
            data={'fields': 'interest.id, interest.is_interest, interest.is_klp_term, '
                            'interest.klp_has_related, interest.url_name'},
            ignore_bookmark=True)
        if response.get('status') == APIStatus.SUCCESS:
            # response.get('data') can be None, e.g. for blacklisted terms
            return response.get('data') or {}
        return {}

    def _get_interest_url(self, interest_info):
        if interest_info.get('url_name'):
            return '/explore/' + interest_info['url_name'] + '/'
        return None

    def get(self):
        # TODO(sdapul): It breaks encapsulation to for this resource to know about
        # the module that called it.  Instead, an option should be passed in explicitly.
        main_module_name, resource_options = self.get_main_module_and_options()
        main_module_name = self.options.get('main_module_name', 'InterestFeedPage')

        response = {}

        if main_module_name == 'InterestFeedPage':
            interest_name = self.options.get('main_module_interest')
            interest_id = url_utils.parse_interest_id(interest_name)
            interest = interest_id if interest_id else interest_name

            interest_response = self._get_interest_info(interest)

            is_klp_term = interest_response.get('is_klp_term')
            is_interest = interest_response.get('is_interest')
            klp_has_related = interest_response.get('klp_has_related')

            # Only show KLP bar on KLP pages, not interest pages
            if (is_klp_term and
                    not is_interest and
                    klp_has_related):
                response = self.request('/v3/interests/%s/related/' % interest_response.get('id'),
                                        field_set_key='annotations',
                                        data={'limit': self.KEYWORD_LIMIT})
        elif main_module_name == 'BoardPage':
            main_module_slug = resource_options.get('slug', self.options.get('main_module_slug'))
            main_module_username = resource_options.get('username', self.options.get('main_module_username'))

            slug = urllib.unquote(main_module_slug).decode('utf-8')
            response = self.request(
                '/v3/boards/%s/%s/interests/' % (main_module_username, slug),
                field_set_key='annotations',
                data={'interest_type': 'extended'})
        elif main_module_name == 'Closeup':
            response = self.request(
                '/v3/pins/%s/interests/' % self.options.get('main_module_id'),
                field_set_key='annotations',
                data={'interest_type': 'extended', 'limit': self.KEYWORD_LIMIT})

        if response.get('status') == APIStatus.SUCCESS:
            if response.get('data'):
                related_interests = response['data']
                response['data'] = {}
                response['data']['related_interests'] = related_interests
                stat_client.increment('event.seo.klp_bar.get_related_interests.%s.success'
                                      % main_module_name, sample_rate=0.001)
            else:
                stat_client.increment('event.seo.klp_bar.get_related_interests.%s.empty'
                                      % main_module_name, sample_rate=0.001)
                # Log when a KLP has no related terms shown so we can investigate
                # Only log for en-us. Related interests are often empty for non-en-us due to a shortage
                # of translated terms.
                if main_module_name == 'InterestFeedPage' and self.context.locale.lower() == 'en-us':
                    return self.response_error("No related interests")

                return response
        else:
            stat_client.increment('event.seo.klp_bar.get_related_interests.%s.failure'
                                  % main_module_name, sample_rate=0.001)

        return response


class InterestTypeaheadResource(BaseResource):
    field_sets = {
        'default': (
            'interest.id',
            'interest.key',
            'interest.name',
            'interest.images[136x136]',
            'interest.follower_count',
            'interest.is_followed',
        ),
        'blur': (
            'interest.background_color',
            'interest.id',
            'interest.key',
            'interest.name',
            'interest.images[300x300(ir.24)]',
            'interest.follower_count',
            'interest.is_followed',
        )
    }

    def _transform_items(self, items):
        for item in items:
            item['label'] = item['name']
            if item['images'] and '136x136' in item['images'] and item['images']['136x136']:
                item['image'] = item['images']['136x136']['url']
            if item['images'] and '300x300(ir.24)' in item['images'] and item['images']['300x300(ir.24)']:
                item['image'] = item['images']['300x300(ir.24)']['url']
            item.pop('name', None)
            item.pop('images', None)

    def get(self):
        data = {
            'query': self.options.get('term'),
            # active_only default to True as a product decision on Dec. 23, 2015
            'active_only': self.options.get('active_only', True),
        }

        response = self.request('/v3/search/interests/', data=data)

        if response['status'] == APIStatus.SUCCESS:
            items = response['data']
            self._transform_items(items)
            response['data'] = {
                'items': items
            }

        return response


class ReactKLPResource(BaseResource):
    def _get_page_size(self):
        if self.options.get('page_size'):
            return self.options['page_size']
        elif self.context.is_bot == 'true':
            return 125
        elif self.context.is_mobile_agent:
            return 8
        else:
            return 25

    def get(self):
        opentsdb_client_v2.increment('denzel.resource.ReactKLPResource.get', sample_rate=0.1,
                                     tags=build_metric_tags(self.context))

        start_time_ms = time_utils.now_millis()

        interest_id = self.options.get('interest_id') or '0'
        is_interest = self.options.get('is_interest') or False
        interest_name = self.options.get('interest_name')

        resp = {'data': {}}

        page_size = self._get_page_size()

        related_interest_size = 20

        base_interests_feed_resource = BaseInterestsFeedResource(self.context,
                                                                 field_set_key='unauth_react',
                                                                 interest=interest_id, add_vase=True,
                                                                 interest_name=interest_name,
                                                                 page_size=page_size)
        related_interests_resource = RelatedInterestsResource(self.context,
                                                              field_set_key='unauth_react',
                                                              interest_id=interest_id,
                                                              limit=related_interest_size,
                                                              is_interest=is_interest)

        barrier = BarrierAll()
        barrier.add_task(base_interests_feed_resource.get)
        is_dictionary_term = interest_id and interest_id != '0'
        if is_dictionary_term:
            barrier.add_task(related_interests_resource.get)

        results = barrier.wait()

        for result in results:
            if result.get('status', APIStatus.SUCCESS) != APIStatus.SUCCESS:
                return result

        resp['data']['interest_feed'] = results[0].get('data', {}).get('results', {})
        resp['data']['search_debug_data'] = results[0].get('data', {}).get('debug', {})
        resp['data']['bookmarks'] = base_interests_feed_resource.get_latest_bookmark()
        resp['data']['related_interests'] = results[1].get('data', {}) if is_dictionary_term else []
        resp['data']['page_size'] = page_size

        if self.options.get('check_is_open', False):
            # if rollout, add the category
            category = self._get_category(interest_id)
            exp_group = unauth_open_utils.activate_exp(self, 'klp', category)
            resp['data']['us_open_group'] = exp_group
            resp['data']['is_open'] = unauth_open_utils.group_is_open(exp_group)
            resp['data']['category'] = category

        end_time_ms = time_utils.now_millis()
        opentsdb_client_v2.timing('denzel.resource.ReactKLPResource.get',
                                  end_time_ms - start_time_ms, sample_rate=0.1,
                                  tags=build_metric_tags(self.context))
        return resp

    def _get_category(self, interest_id):
        if not interest_id:
            return

        category = None

        """
        Returns klp category information stored in Terrapin
        format: '{"repin_category":"ANIMALS","term":"black cats","impression_category":"ANIMALS","lang":0}'
        """
        raw_category = terrapin_thrift_client.terrapin_service_client.single_get(
            ['main_a', 'main_e'],
            'seo_klp_category',
            str(interest_id))

        if raw_category:
            try:
                category_json = json.loads(raw_category)
                category = category_json.get('impression_category', '').lower()
                if category:
                    stat_client.increment('seo.klp.get_category.success', sample_rate=1)
                else:
                    stat_client.increment('seo.klp.get_category.empty_category', sample_rate=1)
            except ValueError:
                stat_client.increment('seo.klp.get_category.json_error', sample_rate=1)
        else:
            stat_client.increment('seo.klp.get_category.empty_raw', sample_rate=1)

        return category


class MainReactKLPResource(InterestResource):
    def get(self):
        opentsdb_client_v2.increment('denzel.resource.MainReactKLPResource.get', sample_rate=0.1,
                                     tags=build_metric_tags(self.context))

        start_time_ms = time_utils.now_millis()

        interest_response = super(MainReactKLPResource, self).get()

        # If we have an error or a redirect URL, return the response as is
        if (interest_response.get('status', APIStatus.SUCCESS) != APIStatus.SUCCESS or
                interest_response.get('data', {}).get('redirect_url')):
            return interest_response
        elif self.context.redirect:
            # If we need to redirect, bail here with empty data.
            return {'data': {}}

        interest_data = interest_response.get('data', {})

        klp_resource = ReactKLPResource(self.context,
                                        interest_id=interest_data['id'],
                                        is_interest=interest_data.get('is_interest', False),
                                        interest_name=interest_data.get('name'),
                                        page_size=self.options.get('page_size'),
                                        check_is_open=self.options.get('check_is_open'))

        response = klp_resource.get()
        if response.get('status', APIStatus.SUCCESS) != APIStatus.SUCCESS:
            return response

        data = response.get('data', {})
        data['interest_data'] = interest_data

        end_time_ms = time_utils.now_millis()
        opentsdb_client_v2.timing('denzel.resource.MainReactKLPResource.get',
                                  end_time_ms - start_time_ms, sample_rate=0.1,
                                  tags=build_metric_tags(self.context))
        return response


class PureReactKLPResource(BaseFeedOfPinsResource):
    def get(self):
        opentsdb_client_v2.increment('denzel.resource.PureReactKLPResource.get', sample_rate=0.1,
                                     tags=build_metric_tags(self.context))

        start_time_ms = time_utils.now_millis()
        interests_resource = InterestResource(self.context,
                                              field_set_key='unauth_react',
                                              interest=self.options.get('interest'),
                                              no_gift_wrap=self.options.get('no_gift_wrap'),
                                              main_module_name=self.options.get('main_module_name'),
                                              experiment=self.options.get('experiment'))
        interests_resource_result = interests_resource.get()
        interest_data = {}
        if interests_resource_result.get('status', None) == APIStatus.SUCCESS:
            # If we know we need to redirect, bail here with empty data.
            if self.context.redirect:
                return {'data': {}}
            if interests_resource_result.get('data'):
                interest_data = interests_resource_result.get('data')

        interest_id = interest_data.get('id')
        is_interest = interest_data.get('is_interest')
        interest_name = interest_data.get('name', '')
        page_size = self.options.get('page_size')
        resp = {'data': {}}

        base_interests_feed_resource = BaseInterestsFeedResource(self.context,
                                                                 field_set_key='unauth_react',
                                                                 interest=interest_id, add_vase=True,
                                                                 interest_name=interest_name,
                                                                 page_size=page_size)
        inspired_wall_resource = NodeResourceStub('InspiredWallResource', self.context, {})
        related_interests_resource = RelatedInterestsResource(self.context,
                                                              field_set_key='unauth_react',
                                                              interest_id=interest_id,
                                                              limit=8,
                                                              is_interest=is_interest)

        barrier = BarrierAll()
        barrier.add_task(base_interests_feed_resource.get)
        barrier.add_task(inspired_wall_resource.get)
        is_dictionary_term = interest_id and interest_id != '0'
        if is_dictionary_term:
            barrier.add_task(related_interests_resource.get)

        results = barrier.wait()

        for result in results:
            if result.get('status', APIStatus.SUCCESS) != APIStatus.SUCCESS:
                return result

        # Make response cachable
        resp['http_status'] = 200
        resp['data']['interest_feed'] = results[0].get('data', {}).get('results', {})
        resp['data']['search_debug_data'] = results[0].get('data', {}).get('debug', {})
        resp['data']['bookmarks'] = base_interests_feed_resource.get_latest_bookmark()
        resp['data']['inspired_wall_story'] = results[1].get('data', {}).get('story', {})
        resp['data']['related_interests'] = results[2].get('data', {}) if is_dictionary_term else []
        resp['data']['interest_data'] = interest_data
        end_time_ms = time_utils.now_millis()
        opentsdb_client_v2.timing('denzel.resource.PureReactKLPResource.get',
                                  end_time_ms - start_time_ms, sample_rate=0.1,
                                  tags=build_metric_tags(self.context))
        return resp

    def get_page_metadata(self):
        interests_resource = InterestResource(self.context,
                                              field_set_key='unauth_react',
                                              interest=self.options.get('interest'),
                                              no_gift_wrap=self.options.get('no_gift_wrap'),
                                              main_module_name=self.options.get('main_module_name'),
                                              experiment=self.options.get('experiment'))

        metadata = interests_resource.get_page_metadata() or {}
        if self.context.is_amp:
            metadata['amp-link-variable-allowed-origin'] = 'https://bnc.lt'

        return metadata
