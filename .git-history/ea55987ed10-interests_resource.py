# -*- encoding: utf-8 -*-
import base64
import copy
import math
import string
import urllib
import zlib

import brotli
import msgpack
import simplejson as json

from collections import namedtuple
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
from config.cache import KLP_INTEREST_PREFIX
from config.cache import KLP_INTEREST_FORMAT
from config.cache import KLP_INTEREST_EXPIRE_TIME_SECONDS
from data_clients.memcache import create_key_gen
from data_clients.memcache import MemcacheClient
from data_clients import terrapin_thrift_client
from logger import kafka_event
from logger.statsd import stat_client
from logger.statsd import opentsdb_client_v2
from services.utils.barrier import BarrierAll
from settings import DEBUG
from settings import IS_EXTERNAL_DEV
from webapp import metatags
from webapp.resources.related_interests_resource import RelatedInterestsResource
from webapp.utils import metatag_keywords
from webapp.resources import seo_utils
from webapp.resources import unauth_open_utils
from webapp.resources.base_resource import APIStatus
from webapp.resources.base_resource import BaseResource
from webapp.resources.feed_resource import BaseFeedOfInterestsResource
from webapp.resources.feed_resource import BaseFeedOfPinsResource
from webapp.resources.node_resource_stub import NodeResourceStub
from webapp.resources.pin_resource import PinResource
from webapp.utils import app_interstitial

INTEREST_FEED_RESOURCE_BATCH_EXPR = 'pin_join_manager_batch'

klp_feed_cache = MemcacheClient(
    KLP_FEED_CONN,
    create_key_gen(KLP_FEED_PREFIX, KLP_FEED_FORMAT, force_hash=True),
    KLP_FEED_EXPIRE_TIME_SECONDS)

interest_cache = MemcacheClient(
    KLP_INTEREST_CONN,
    create_key_gen(KLP_INTEREST_PREFIX, KLP_INTEREST_FORMAT, force_hash=True),
    KLP_INTEREST_EXPIRE_TIME_SECONDS)

SEO_FAKE_KLP = 'seo_fake_klp_log'


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
            'interest.is_interest',
            'interest.is_klp_term',
            'interest.images[orig]',
            'interest.url_name',
            'interest.breadcrumbs',
            'interest.translation_urls',
        )
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
        use_cache = ((decider.decide_experiment('klp_interest_cache') and
                      self.context.experiments.v2_activate_experiment('interest_cache') != 'disabled') and
                     self.context.is_full_page)
        skip_cache = (self.context.experiments.v2_activate_experiment('interest_cache') == 'invalidate' or
                      decider.decide_experiment('klp_interest_cache_invalidate'))
        return use_cache, skip_cache

    def _get_cached_response(self, interest, field_set_key, skip_cache):
        cache_key = (interest, self.context.locale.lower(), field_set_key)
        if not skip_cache:
            cached_result = interest_cache.get(cache_key)
            if cached_result:
                return cache_key, msgpack.unpackb(cached_result, encoding="utf-8")
        return cache_key, None

    def get(self):
        # If in the auth KLP search group v2 short circuit resource to avoid network call if we can parse interest_name
        main_module_name = self.options.get('main_module_name', '')
        in_auth_klp_search_v2 = self.context.experiments.v2_in_group('web_usm_auth_klp_refresh', ['enabled_search_v2'])
        eligible_for_klp_search_v2 = (not self.context.is_mobile_agent and
                                      main_module_name == 'InterestFeedPage' and in_auth_klp_search_v2)

        if eligible_for_klp_search_v2:
            interest_name = url_utils.parse_interest_name(self.options['interest'])
            if interest_name:
                return {'data': {'name': interest_name}}

        start_time_ms = time_utils.now_millis()
        if self.options['interest'] is not None:
            self.options['interest'] = self.options['interest'].lower()
        interest_id = url_utils.parse_interest_id(self.options['interest'])
        interest = interest_id if interest_id else self.options['interest']
        field_set_key = self.get_field_set_key()
        resp = None
        use_cache, skip_cache = self._get_cache_settings()

        if use_cache:
            cache_key, resp = self._get_cached_response(interest, field_set_key, skip_cache)

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

            is_debug_mode = False
            if self.context.request_debug and self.context.request_debug.get('deb_d'):
                is_debug_mode = True
                resp['data']['is_debug_mode'] = True

            # For unauth and 'no_gift_wrap=true' we won't show gift wrap. This is necessary for KLP Pipeline
            # when we use human eval for feed relevance.
            if not self.context.is_authenticated and (self.options.get('no_gift_wrap') == 'true' or is_debug_mode):
                resp['data']['no_gift_wrap'] = True

            # only cache results for terms in the dictionary
            is_dictionary_term = data.get('id') and data.get('id') != '0'
            if use_cache and is_dictionary_term:
                interest_cache.set(cache_key, msgpack.packb(resp, use_bin_type=True, encoding="utf-8"))

        if (not self.context.is_authenticated and data.get('name')
                and string.capwords(data.get('name')) == data.get('name')):
            group = self.context.activate_seo_or_unauth_experiment('klp_title_format_change')
            if group and group.startswith('enabled'):
                data['name'] = string.capitalize(data.get('name').lower())

        determine_explore_redirect(data, self.options.get('interest'), self.context, resp)
        if self.context.redirect:
            return resp

        if not data.get('is_klp_term'):
            resp['data'] = {
                'id': '0',
                'name': data.get('name', ''),
                'is_interest': data.get('is_interest', False),
                'is_klp_term': data.get('is_klp_term', False),
            }
            stat_client.increment('seo.klp.non_klp_term', sample_rate=1)
            kafka_event.log_as_json(SEO_FAKE_KLP, {'name': data.get('name', ""), 'locale': self.context.locale})
            return resp

        end_time_ms = time_utils.now_millis()
        opentsdb_client_v2.timing('denzel.resource.InterestResource.get',
                                  end_time_ms - start_time_ms, sample_rate=0.05,
                                  tags=build_metric_tags(self.context))

        name = data.get('name')
        if self.ja_enabled_editorial_klps.contains(name):
            resp['data']['description'] = self.ja_enabled_editorial_klps.get(name)

        return resp

    def _get_interest_for_metadata(self, interest, field_set_key):
        response = None
        cache_hit = True
        start_time_ms = time_utils.now_millis()
        use_cache, skip_cache = self._get_cache_settings()
        if use_cache and not skip_cache:
            _, response = self._get_cached_response(interest, field_set_key, skip_cache)

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
            interest_data = response.get('data', {})

            canonical_term_id = (interest_data.get('canonical_term') or {}).get('id', 0)
            if canonical_term_id and canonical_term_id != int(interest_data.get('id')):
                response = self._get_interest_for_metadata(str(canonical_term_id), field_set_key)
                if response.get('status') == APIStatus.SUCCESS:
                    interest_data = response.get('data', {})

            # This could happen if the interest is a banned term
            if not interest_data:
                return {'robots': 'noindex'}

            metadata = metatags.get_interest_metadata(
                self.context.get('full_path'),
                interest_data.get('name'),
                interest_data.get('images', {}).get('orig', {}).get('url'))

            # We don't want non-dictionary terms to be indexed, even if we need
            # to continue to support certain pages that have already been
            # linked to in hashtag descriptions and followed by users
            # NOTE: this was originally is_seo, but we changed it when we
            # we removed "seo" from our client-visable source
            if not interest_data.get('is_klp_term'):
                metadata['robots'] = 'noindex'

            metatag_keywords.update_with_keywords(self, metadata, interest_id=interest_data.get('id'))

            metatags.update_title_text(metadata)
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


def determine_explore_redirect(data, interest, context, resp):
    if not data.get('is_klp_term'):
        if context.experiments.v2_activate_experiment('vase_carousel_explore_links') == 'holdout':
            stat_client.increment('seo.klp.redirect.search', sample_rate=1)
            context.redirect = '/search/?q=' + urllib.quote(interest.encode('utf-8'))
            return
    if int(data.get('id')) and context.is_full_page:
        context['canonical_url'] = data.get('canonical_url')
        if context['canonical_url'] != '/explore/%s/' % interest.replace(' ', '-'):
            options = []
            if 'nogw=true' in context['full_path']:
                options.append("nogw=true")
            if options:
                context.redirect = "%s?%s" % (context['canonical_url'],
                                              "&".join(options))
            else:
                context.redirect = context['canonical_url']
            stat_client.increment('seo.klp.redirect.canonical', sample_rate=1)


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
Offsets = namedtuple('offsets', ['relative_start_index', 'relative_end_index',
                                 'num_pages_needed', 'initial_cache_page_bookmark', 'next_client_offset'])


class BaseInterestsFeedResource(BaseResource):

    default_field_set_key = 'pins'
    field_sets = {
        'pins': BaseFeedOfPinsResource.field_sets['interest_grid_item'],
        'unauth_react': PinResource.field_sets['unauth_react_grid_item']
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

    def _get_api_and_cache_bookmarks(self, combined_bookmark, identifier):
        if combined_bookmark:
            if combined_bookmark[:3] == identifier:
                combined_bookmark = base64.b64decode(combined_bookmark[3:])
        if combined_bookmark is None:
            api_bookmark = None
            client_offset = 0
        elif ',' not in combined_bookmark:
            api_bookmark = combined_bookmark
            client_offset = None
        else:
            bookmarks = combined_bookmark.split(',', 1)
            api_bookmark = bookmarks[1]
            try:
                client_offset = int(bookmarks[0])
            except ValueError:
                client_offset = None
            if api_bookmark == 'None':
                api_bookmark = None
        return api_bookmark, client_offset

    def _get_offsets(self, absolute_start_index, cache_page_size, client_page_size):
        if absolute_start_index is None:
            absolute_start_index = 0
        relative_start_index = absolute_start_index % cache_page_size
        relative_end_index = (relative_start_index + client_page_size)
        num_pins_from_first_page = cache_page_size - relative_start_index
        remaining_pins_needed = client_page_size - num_pins_from_first_page
        num_pages_needed = int(1 + math.ceil(float(remaining_pins_needed) / float(cache_page_size)))
        initial_cache_page_bookmark = int(absolute_start_index/cache_page_size) * cache_page_size
        next_client_offset = absolute_start_index + client_page_size
        return Offsets(relative_start_index, relative_end_index, num_pages_needed,
                       initial_cache_page_bookmark, next_client_offset)

    def _get_cached_klp_feed(self, interest_id, interest_key):
        default_page_size = 125 if (self.context.is_bot == 'true') else 25
        start_time_ms = time_utils.now_millis()
        cache_hit = True
        experiments = ':devapp:%d' % (DEBUG or IS_EXTERNAL_DEV) if (DEBUG or IS_EXTERNAL_DEV) else ''

        # Use running experiments from ngapi. Should be in sync with core/logic/seo_logic.py
        # The loop does nothing when there're no active experiments.
        # It's kept here to make sure it would be used for all new experiments.
        for seo_experiment in ('unauth_ranking_klp_holdout', 'unauth_ranking_klp_v2'):
            group = self.context.activate_seo_or_unauth_experiment(seo_experiment)

            # Do not use control in the cache key
            if group and not group.startswith('control'):
                experiments += ':%s=%s' % (seo_experiment, group)

        debug_data = {}
        if self.context.request_debug:
            debug_data.update(self.context.request_debug)

        field_set_key = self.get_field_set_key()
        vase_key = self.options.get('add_vase') and self.context.language in seo_utils.VISUAL_DESCRIPTION_LANGUAGES

        locales_to_use_cache = ['en-us', 'de', 'fr', 'pt-br', 'en-gb', 'en-in', 'es-es', 'es-mx', 'en-ca']
        client_page_size = self.options.get('page_size', default_page_size)
        cache_page_size = 25
        combined_bookmark = self.get_latest_bookmark()
        identifier = 'cb:'
        api_bookmark, client_offset = self._get_api_and_cache_bookmarks(combined_bookmark, identifier)
        use_cache = (interest_id and
                     decider.decide_experiment('klp_feed_cache') and
                     self.context.experiments.v2_activate_experiment('klp_cache') != 'disabled' and
                     self.context.locale.lower() in locales_to_use_cache)
        skip_cache = (self.context.experiments.v2_activate_experiment('klp_cache') == 'invalidate' or
                      client_offset is None or
                      decider.decide_experiment('klp_feed_cache_invalidate'))

        offsets = self._get_offsets(client_offset, cache_page_size, client_page_size)
        relative_start_index, relative_end_index, num_pages_needed, initial_cache_page_bookmark,\
            next_client_offset = offsets
        cumulative_data = []
        cache_keys = []
        for i in range(num_pages_needed):
            cache_page_bookmark = (initial_cache_page_bookmark + (i * cache_page_size))
            cache_key = (interest_id, self.context.locale.lower(), cache_page_bookmark,
                         1 if vase_key else 0, field_set_key, experiments)
            cache_keys.append(cache_key)

        temp_multiple_results = klp_feed_cache.get_many(cache_keys) if use_cache and not skip_cache else None

        if temp_multiple_results and len(temp_multiple_results) == num_pages_needed:
            # get from cache
            temp_cumulative_data = []
            for k, v in temp_multiple_results.iteritems():
                try:
                    result = msgpack.unpackb(brotli.decompress(v), encoding="utf-8")
                except brotli.error:
                    result = json.loads(zlib.decompress(v))
                result_cache_offset = result['cache_key'][2]
                temp_cumulative_data.append((result_cache_offset, result['data']))
            sorted_data = sorted(temp_cumulative_data, key=lambda result: result[0])
            cumulative_data = [item for sub_tuple in sorted_data for item in sub_tuple[1]]
        else:
            # Get from API
            cache_hit = False
            debug_data.update({'page_size': cache_page_size})
            debug_data.update({'bookmark': api_bookmark})
            for i in range(num_pages_needed):
                kwargs = {'data': debug_data}
                if 'fields' not in debug_data:
                    kwargs['field_set_key'] = field_set_key
                result = self.request("/v3/klp/%s/feed/" % interest_key, **kwargs)
                if result and result.get('data') and result.get('status') == APIStatus.SUCCESS:
                    data = self._filter_duplicate_images(result.get('data'))
                    if data and data[0].get('id'):
                        first_pin_id = data[0].get('id')
                    else:
                        first_pin_id = None
                    if self.options.get('add_vase') and self.context.language in seo_utils.VISUAL_DESCRIPTION_LANGUAGES:
                        self._get_visual_data(data)
                    if use_cache and first_pin_id:
                        cache_page_bookmark = (initial_cache_page_bookmark + (i * cache_page_size))
                        cache_key = (interest_id, self.context.locale.lower(), cache_page_bookmark,
                                     1 if vase_key else 0, field_set_key, experiments)
                        result['cache_key'] = cache_key
                        klp_feed_cache.set(cache_key, brotli.compress(msgpack.packb(result,
                                                                                    encoding="utf-8"), quality=1))
                cumulative_data.extend(result['data'])
                debug_data.update({'bookmark': result.get('bookmark')})

        api_bookmark = result.get('bookmark')
        result['data'] = cumulative_data[relative_start_index:relative_end_index]

        combined_bookmark = identifier + base64.b64encode(str(next_client_offset) + ',' + str(api_bookmark))
        self.add_bookmark(combined_bookmark)

        if result.get('data'):
            if (self.context.is_full_page and
                    self.context.get_seo_experiment_group('klp_rich_snippet', skip_logging=True) != 'control_4'):
                seo_utils.show_rich_snippet_pin(self, result['data'], ('enabled_klp'))

        # discovery_debug expects a certain object structure, repackage
        newData = {}
        newData['results'] = result.get('data')

        if result.get('debug_data'):
            newData['debug'] = result.get('debug_data')

        result['data'] = newData
        if result.get('status') == APIStatus.SUCCESS:
            opentsdb_client_v2.timing('denzel.resource.InterestsFeedResource.get',
                                      time_utils.now_millis() - start_time_ms, sample_rate=0.05,
                                      tags=build_metric_tags(self.context, {'cached': str(cache_hit)}))
        return result

    def get(self):
        interest = self.options.get("interest")
        if not interest:
            return self.response_error("Empty interest field")

        interest_id = url_utils.parse_interest_id(interest)
        # pass a key derived from interest name when interest_id is missing (for non-dictionary terms)
        # if interest name is blank, pass '0' (the string), so the klp API call succeeds
        interest_key = (interest_id or
                        self.options.get('interest_name', '').lower().replace(' ', '-') or
                        '0')

        return self._get_cached_klp_feed(interest_id, interest_key)


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

        feed_type = self.options.get("feed_type", 'prod')

        debug_on = False
        if self.context.request_debug:
            # Debug parameters used for interest feeds
            feed_type = self.context.request_debug.get('deb_feed')
            if self.context.request_debug.get('deb_d') == "True":
                debug_on = True
        response = self.request("/v3/interests/%s/feed/" % interest,
                                data={'feed_type': feed_type, 'debug_on': debug_on})

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

    def get(self):
        start_time_ms = time_utils.now_millis()
        interest_id = self.options['interest_id']
        is_interest = self.options.get('is_interest', False)
        resp = {'data': {}}

        page_size = self.options.get('page_size', 25)

        base_interests_feed_resource = BaseInterestsFeedResource(self.context,
                                                                 field_set_key='unauth_react',
                                                                 interest=interest_id, add_vase=True,
                                                                 interest_name=self.options.get('interest_name'),
                                                                 page_size=page_size)
        related_interests_resource = RelatedInterestsResource(self.context,
                                                              field_set_key='unauth_react',
                                                              interest_id=interest_id,
                                                              limit=20,
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

        if self.options.get('check_is_open', False):
            # if rollout, add the category
            category = self._get_category(self.options.get('interest_id'))
            exp_group = unauth_open_utils.activate_exp(self, 'klp', category)
            resp['data']['us_open_group'] = exp_group
            resp['data']['is_open'] = unauth_open_utils.group_is_open(exp_group)

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


class PureReactKLPResource(BaseFeedOfPinsResource):
    def get(self):
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
                                                              field_set_key='react',
                                                              interest_id=interest_id,
                                                              limit=20,
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
        return interests_resource.get_page_metadata()
