import re
import logging
import urlparse

from common.utils import cookie_utils
from common.utils import country_domain_utils
from common.utils import data_structure_utils
from common.utils import decider
from common.utils import seo_signal_utils
from common.utils import time_utils
from common.utils.seo_utils import build_metric_tags
from common.utils.seo_utils import get_refer_type, SEARCH_ENGINES
from logger import kafka_event
from logger.statsd import opentsdb_client_v2
from logger.statsd import stat_client
from schemas.event_if.ttypes import EventType
from services.utils.barrier import BarrierAll
from settings import CANONICAL_MAIN_DOMAIN
from webapp import metatags
from webapp.resources import seo_utils
from webapp.resources.base_resource import APIStatus
from webapp.resources.base_resource import BaseResource
from webapp.resources.context_log_resource import EventLogInfo
from webapp.resources.decorators import log_context
from webapp.resources.decorators import require_explicit_login
from webapp.resources.pin_comments_resource import PinCommentResource
from webapp.resources.product_resource import WEB_ACCESS_GROUPS
from webapp.resources.user_resource import UserResource
from webapp.utils import app_interstitial
from webapp.utils import metatag_keywords

log = logging.getLogger(__name__)

pin_page_regex = re.compile(r'^(/amp)?/pin/[0-9]+/(\?[^/]+)?$')
seo_pin_id_regex = re.compile(r'^[^\/_]+--[0-9]+$')

SEARCH_GUIDES_LIMIT = 25

PARTNER_UPLOAD_SOURCE = 'partner_upload_standalone'

react_grid_pin_field_set = (
    'pin.access',
    'pin.attribution',
    'pin.aggregated_pin_data()',
    'pin.board()',
    'pin.description',
    'pin.domain',
    'pin.dominant_color',
    'pin.embed',
    'pin.has_required_attribution_provider',
    'pin.id',
    'pin.image_signature',
    'pin.images[136x136,236x,474x,736x,orig]',
    'pin.is_downstream_promotion',
    'pin.is_promoted',
    'pin.is_quick_promotable',
    'pin.like_count',
    'pin.liked_by_me',
    'pin.link',
    'pin.pinner()',
    'pin.promoter()',
    'pin.repin_count',
    'pin.rich_summary()',
    'pin.title',
    'pin.type',
    'pin.buyable_product()',
    'pin.videos()',

    'aggregatedpindata.aggregated_stats',
    'aggregatedpindata.id',
    'aggregatedpindata.pin_tags',

    'board.id',
    'board.name',
    'board.owner()',
    'board.url',
    'board.followed_by_me',

    'video.video_list[V_HLSV4,V_720P]',
    'video.id',

    'buyableproductmetadata.display_active_max_price',
    'buyableproductmetadata.display_active_min_price',
    'buyableproductmetadata.short_description',
    'buyableproductmetadata.title',
)

grid_item_field_set = (
    'pin.access',
    'pin.attribution',
    'pin.additional_hide_reasons',
    'pin.aggregated_pin_data()',
    'pin.ad_match_reason',
    'pin.board()',
    'pin.comment_count',
    'pin.comments(limit:5,resume:true)',
    'pin.created_at',
    'pin.debug_info_html',
    'pin.description',
    'pin.description_html',
    'pin.domain',
    'pin.dominant_color',
    'pin.embed',
    'pin.grid_description',
    'pin.has_required_attribution_provider',
    'pin.id',
    'pin.image_signature',
    'pin.images[136x136,236x,474x,736x,orig]',
    'pin.is_downstream_promotion',
    'pin.is_eligible_for_web_closeup',
    'pin.is_playable',
    'pin.is_promoted',
    'pin.is_quick_promotable',
    'pin.is_repin',
    'pin.is_uploaded',
    'pin.is_video',
    'pin.like_count',
    'pin.liked_by_me',
    'pin.link',
    'pin.method',
    'pin.pinner()',
    'pin.price_currency',
    'pin.price_value',
    'pin.privacy',
    'pin.promoter()',
    'pin.repin_count',
    'pin.rich_summary()',
    'pin.title',
    'pin.type',
    'pin.view_tags',
    'pin.buyable_product()',
    'pin.videos()',

    'aggregatedpindata.aggregated_stats',
    'aggregatedpindata.id',
    'aggregatedpindata.pin_tags',

    'board.id',
    'board.image_thumbnail_url',
    'board.is_collaborative',
    'board.layout',
    'board.name',
    'board.owner()',
    'board.privacy',
    'board.type',
    'board.url',
    'board.followed_by_me',

    'user.explicitly_followed_by_me',
    'user.full_name',
    'user.id',
    'user.image_large_url',
    'user.image_small_url',
    'user.type',
    'user.username',
    'video.video_list[V_HLSV4,V_720P]',
    'video.id',

    'buyableproductmetadata.display_active_max_price',
    'buyableproductmetadata.display_active_min_price',
    'buyableproductmetadata.short_description',
    'buyableproductmetadata.title',
)


class PinResource(BaseResource):

    default_field_set_key = 'summary'
    field_sets = {
        'grid_item': grid_item_field_set + PinCommentResource.field_sets['pin_grid_item'],

        'partner_grid_item': (
            'pin.is_promotable',
            'pin.per_pin_analytics()',
        ) + grid_item_field_set,

        'react_grid_pin': react_grid_pin_field_set,

        'partner_react_grid_pin': (
            'pin.is_promotable',
            'pin.per_pin_analytics()',
        ) + react_grid_pin_field_set,

        'summary': (
            'pin.access',
            'pin.aggregated_pin_data()',
            'pin.attribution',
            'pin.board()',
            'pin.comment_count',
            'pin.created_at',
            'pin.description',
            'pin.description_html',
            'pin.domain',
            'pin.dominant_color',
            'pin.embed',
            'pin.grid_description',
            'pin.has_required_attribution_provider',
            'pin.id',
            'pin.images[236x,474x,736x]',
            'pin.is_playable',
            'pin.is_repin',
            'pin.is_uploaded',
            'pin.is_video',
            'pin.like_count',
            'pin.liked_by_me',
            'pin.link',
            'pin.method',
            'pin.pinner()',
            'pin.price_currency',
            'pin.price_value',
            'pin.repin_count',
            'pin.rich_summary()',
            'pin.title',
            'pin.type',
            'pin.via_pinner()',

            'aggregatedpindata.aggregated_stats',
            'aggregatedpindata.id',

            'board.id',
            'board.image_cover_url',
            'board.layout',
            'board.name',
            'board.owner',
            'board.pin_thumbnail_urls',
            'board.type',

        ) + UserResource.field_sets['summary'],

        'add_to_map_modal': (
            'pin.board()',
            'pin.description',
            'pin.id',
            'pin.images[136x136]',
            'pin.type',

            'board.id',
        ),

        'infer_rich_pin': (
            'pin.id',
        ),

        'edit': (
            'pin.access',
            'pin.board()',
            'pin.description',
            'pin.id',
            'pin.is_repin',
            'pin.is_video',
            'pin.images[236x,736x]',
            'pin.link',
            'pin.link_domain()',
            'pin.pinner()',
            'pin.type',

            'board.id',
            'board.name',
            'board.privacy',
            'board.type',
            'board.url',

            'user.full_name',
            'user.id',
            'user.image_small_url',
            'user.type',
            'user.username',

            'domain.official_user()',
        ),

        'action_bar': (
            'pin.description',
            'pin.id',
            'pin.images[236x,orig]',
            'pin.is_video',
            'pin.like_count',
            'pin.liked_by_me',
            'pin.link',
            'pin.privacy',
            'pin.repin_count',
            'pin.type',
        ),

        'closeup_share': (
            'pin.description',
            'pin.id',
            'pin.images[236x,736x]',
            'pin.type',
        ),

        'share_email': (
            'pin.id',
            'pin.images[236x,736x]',
            'pin.type',
        ),

        'detailed': (
            'pin.access',
            'pin.aggregated_pin_data()',
            'pin.attribution',
            'pin.buyable_product()',
            'pin.buyable_product_availability()',
            'pin.board()',
            'pin.category',
            'pin.closeup_description',
            'pin.closeup_user_note',
            'pin.comment_count',
            'pin.created_at',
            'pin.description',
            'pin.description_html',
            'pin.domain',
            'pin.dominant_color',
            'pin.embed',
            'pin.has_required_attribution_provider',
            'pin.hashtags()',
            'pin.id',
            'pin.image_signature',
            'pin.images[60x60,136x136,170x,236x,474x,564x,736x,600x315,orig]',
            'pin.is_playable',
            'pin.is_promoted',
            'pin.is_repin',
            'pin.is_video',
            'pin.like_count',
            'pin.liked_by_me',
            'pin.link',
            'pin.link_domain()',
            'pin.method',
            'pin.pinner()',
            'pin.title',
            'pin.price_currency',
            'pin.price_value',
            'pin.privacy',
            'pin.promoter()',
            'pin.repin_count',
            'pin.rich_metadata()',
            'pin.rich_recipe_top_ingredients',  # for recipe pages
            'pin.tracked_link',
            'pin.type',
            'pin.via_pinner()',
            'pin.origin_pinner()',
            'pin.videos()',

            'aggregatedpindata.aggregated_stats',
            'aggregatedpindata.id',
            'aggregatedpindata.pin_tags',

            'board.access',
            'board.category',
            'board.description',
            'board.id',
            'board.image_cover_url',
            'board.image_thumbnail_url',
            'board.is_collaborative',
            'board.followed_by_me',
            'board.layout',
            'board.map_id',
            'board.name',
            'board.owner()',
            'board.pin_thumbnail_urls',
            'board.privacy',
            'board.type',
            'board.url',

            "domain.official_user()",

            'user.domain_url',
            'user.first_name',
            'user.followed_by_me',
            'user.full_name',
            'user.id',
            'user.image_medium_url',
            'user.indexed',
            'user.twitter_url',
            'user.type',
            'user.username',

            'imagemetadata.canonical_images[474x, 564x, 736x, 96x96, 140x140, 280x280, orig]',

            'makecardtutorialview.images[550x,200x]',
            'makecardtutorialinstructionview.images[550x,200x]',

            'video.video_list[V_HLSV4,V_720P]',
            'video.id'
        ) + PinCommentResource.field_sets['pin_detailed']
          + UserResource.field_sets['thumb'],

        'closeup_image': (
            'pin.id',
            'pin.images[736x,orig]',
            'pin.type',
        ),

        'closeup_sidebar': (
            'pin.board()',
            'pin.domain',
            'pin.id',
            'pin.images[60x60,236x,474x,736x,600x315,orig]',
            'pin.pinner()',  # pinner needs to be specified here in the case where
                             # board.owner.id != pinner.id otherwise board data will be None
            'pin.type',
            'pin.rich_metadata()',
            'pin.rich_recipe_top_ingredients',  # for recipe pages
            'board.access',
            'board.followed_by_me',
            'board.id',
            'board.is_collaborative',
            'board.layout',
            'board.name',
            'board.owner()',
            'board.privacy',
            'board.type',
            'board.url',
        ),

        'closeup_pins_grid_item': (
            'pin.id',
            'pin.images[192x]',
            'pin.type'
        ),

        'board_pins_grid_item': (
            'pin.id',
            'pin.images[70x]',
            'pin.type'
        ),

        'board_cover_picker': (
            'pin.id',
            'pin.images[236x]',
            'pin.type',
        ),

        'pinned_to_board': (
            'pin.board()',
            'pin.id',
            'pin.pinned_to_board()',
            'pin.type',
            'pin.via_pinner()',
        ),

        'repin': (
            'pin.description',
            'pin.dominant_color',
            'pin.description_html',
            'pin.id',
            'pin.images[236x,474x,736x]',
            'pin.is_video',
            'pin.link',
            'pin.link_domain()',
            'pin.pinned_to_board()',
            'pin.type',

            'board.id',
            'board.name',
            'board.type',
            'board.url',

            'domain.official_user()',

            'user.follower_count',
        ),

        'flag_pin': (
            'pin.board()',
            'pin.pinner()',
            'pin.id',
            'pin.rich_metadata()',

            'board.id',
            'board.followed_by_me',
            'board.collaborated_by_me',

            'user.id',
            'user.full_name',
            'user.first_name',
            'user.followed_by_me',
            'user.blocked_by_me',

        ) + UserResource.field_sets['thumb'],

        'flag_comment': (
            'pin.board()',
            'pin.pinner()',
            'pin.id',

            'board.id',
            'board.followed_by_me',
            'board.collaborated_by_me',
            'board.owner()',

            'user.id',
        ) + UserResource.field_sets['thumb'],

        'create_success': (
            'pin.board()',
            'pin.domain',
            'pin.id',
            'pin.link_domain()',
            'pin.type',

            'board.category',
            'board.id',
            'board.image_cover_url',
            'board.images[170x]',
            'board.is_collaborative',
            'board.name',
            'board.privacy',
            'board.type',
            'board.url',

            'domain.official_user()',

            'user.explicitly_followed_by_me',
            'user.id',
            'user.follower_count',
            'user.full_name',
            'user.image_small_url',
            'user.username',
        ),

        'table_row': (
            'pin.description',
            'pin.id',
            'pin.images[136x136]',
            'pin.rich_summary()',
        ),

        'promoted_pin_header': (
            'pin.description',
            'pin.id',
            'pin.images[70x,136x136]',  # TODO(tracy) remove 70x after 1.2 launches
            'pin.link',
            'pin.rich_summary()',
            'pin.creative_types',
            'pin.pinner()',

            'user.id',
        ) + UserResource.field_sets['thumb'],

        'promoted_pin_spec_form': (
            'pin.link',
        ),

        'promoted_pin_description': (
            'pin.description',
            'pin.rich_summary()',
        ),

        'rss_item': (
            'pin.created_at',
            'pin.description',
            'pin.description_html',
            'pin.id',
            'pin.images[236x]',
        ),

        'quick_promote_info': (
            'pin.id',
            'pin.is_quick_promotable',
        ),

        'follow_grid_item': (
            'pin.images[236x]',
        ),

        'unauth_react_grid_item': (
            'pin.attribution',
            'pin.board()',
            'pin.comment_count',
            'pin.created_at',
            'pin.description',
            'pin.description_html',
            'pin.domain',
            'pin.dominant_color',
            'pin.has_required_attribution_provider',
            'pin.id',
            'pin.images[170x, 236x, 474x, 564x, 736x, orig]',
            'pin.image_signature',
            'pin.like_count',
            'pin.link',
            'pin.repin_count',
            'pin.title',
            'pin.type',
            'pin.rich_metadata()',
            'pin.rich_summary()',
            'pin.url_tags',

            'richpingriddata.display_name',
            'richpingriddata.apple_touch_icon_images',
            'richpingriddata.favicon_images',
            'richpingriddata.site_name',
            'richpingriddata.type_name',
        ),


        'browser_extension_upsell_grid_item': (
            'pin.images[236x]',
            'pin.domain',
        ),
    }

    #  This is not the conventional way of setting field sets,
    #  but for the purpose of server-side Closeup and Homefeed rendering
    #  which cannot check for experiment logic in the routing page,
    #  we must include additional field sets
    experiments_additional_field_sets = {
        'gator': (
            'pin.aggregated_pin_data()',
            'pin.closeup_description',
            'pin.closeup_user_note',
            'pin.grid_description',

            'aggregatedpindata.aggregated_stats',
            'aggregatedpindata.id',
        ),

        'did_it': (
            'pin.done_by_me',

            'aggregatedpindata.did_it_data()',
        ),

        'web_commerce_grid': (
            'buyableproductmetadata.product_thumbnails',
            'imagemetadata.canonical_images[96x96]',
        )
    }

    field_sets['grid_item_with_rec'] \
        = field_sets['grid_item'] \
        + ('pin.recommendation_reason', 'pin.source_interest()', 'interest.id',
           'interest.images[60x60]', 'interest.name', 'interest.url_name',
           'interest.type')

    field_sets['grid_item_in_bag'] \
        = field_sets['grid_item'] \
        + ('buyableproductmetadata.display_active_max_price', 'buyableproductmetadata.display_active_min_price',
           'buyableproductmetadata.has_free_shipping', 'buyableproductmetadata.has_swatches',
           'buyableproductmetadata.items', 'buyableproductmetadata.merchant_name',
           'buyableproductmetadata.title', 'buyableproductmetadata.variations',
           'domain.official_user()', 'imagemetadata.canonical_images[474x,564x,736x,96x96, 140x140, 280x280, orig]',
           'pin.link_domain()', 'pin.rich_metadata()', 'user.image_medium_url')

    field_sets['grid_item_with_attributions'] \
        = field_sets['grid_item_with_rec'] \
        + ('pin.pin_attribution',)

    field_sets['interest_grid_item'] = \
        field_sets['grid_item'] + ('pin.source_interest()', 'interest.id',
                                   'interest.images[60x60]',
                                   'interest.name', 'interest.url_name')

    field_sets['promo_grid_item'] = \
        ('pin.images[75x75,236x,474x,736x,orig]',) + field_sets['grid_item']

    field_sets['unauth_react_pin'] = \
        field_sets['unauth_react_grid_item'] + ('pin.rich_metadata()',)

    def get_field_set(self):
        """Override"""
        fields = super(PinResource, self).get_field_set()

        if self.options.get('fetch_visual_search_objects'):
            fields += ('pin.visual_objects()',)

        field_set_key = self.options.get('field_set_key', self.default_field_set_key)
        if field_set_key in ('detailed', 'grid_item', 'react_grid_pin'):
            fields += self.experiments_additional_field_sets['did_it']

        if field_set_key == 'detailed' and not self.context.is_authenticated and \
                            (self.context.experiments.v2_get_group('unauth_category_pivot_v2') in
                                ['employees', 'enabled_signup', 'enabled_full_page', 'open', 'control'] or
                             self.options.get('check_is_open', False)):
            fields += ('pin.has_bad_category', 'pin.category',)

        if field_set_key == 'detailed' and not self.context.is_authenticated and \
                            (self.context.experiments.v2_get_group('unauth_male_signup') in
                                ('employees', 'enabled_signup', 'control')):
            if 'pin.category' in fields:
                fields += ('pin.has_male_category',)
            else:
                fields += ('pin.has_male_category', 'pin.category',)
        if field_set_key == 'detailed' and not self.context.is_authenticated:
            fields += ('pin.url_tags',)
        return fields

    def _redirect(self, canonical_pin_id):
        """Redirect the deleted pin to its canonical pin."""
        canonical_pin_url = '/pin/%s/' % canonical_pin_id
        if canonical_pin_url != self.context.full_path:
            stat_client.increment(
                'event.seo.delete_pin_redirect.success')
            self.context.redirect = canonical_pin_url

    def _log_paid_acq_session_metric(self):
        """Log real time traffic metrics for Facebook paid acquisition."""
        parsed_url = urlparse.urlparse(self.context.current_url)
        queries = urlparse.parse_qs(parsed_url.query or '')
        referrer = self.options.get('original_referrer') or self.context.http_referrer or ''
        if (queries.get('ptrf') or [''])[0] == 'atp2':
            netloc = parsed_url.netloc
            category = (queries.get('category') or [''])[0] or 'uncategorized'
            from_campaign = 'from_campaign' if (queries.get('campaign') or [''])[0] == 'true' else 'not_from_campaign'
            from_fb = 'from_facebook' if 'facebook' in (referrer) else 'not_from_facebook'

            metric = 'event.seo.paid_acq.fb.{netloc}.{category}.{from_campaign}.{from_fb}'.format(
                netloc=netloc, category=category, from_campaign=from_campaign, from_fb=from_fb)
            # Apparently resource is called twice when loading a pin, so when viewing the metric we need to divide by 2.
            stat_client.increment(metric, sample_rate=1)

    def _auth_plp_refresh_experiment_gating(self):
        # Pure react will sometimes prepend an internal routing to the referrer. This needs to be removed when checking
        # for the actual referrer.
        # Example
        # Denzel Referrer - "https://www.google.com"
        # Pure React Referrer - "www.pintrest.com,https://www.google.com"
        referrers = (self.options.get('original_referrer') or self.context.http_referrer or '').split(',')
        is_search_engine = any(get_refer_type(referrer)[0] in SEARCH_ENGINES for referrer in referrers)
        if is_search_engine and self.context.is_authenticated:
            if self.context.is_mobile_agent:
                return self.context.experiments.v2_activate_experiment('mweb_usm_auth_plp_refresh')
            else:
                return self.context.experiments.v2_activate_experiment('web_usm_auth_plp_refresh_v2')

    def _auth_plp_format_data(self, response):
        formatted_data = {}
        formatted_data['category'] = response.get('category', None)
        formatted_data['query'] = response.get('query', '')
        formatted_data['guides'] = response.get('terms', [])
        formatted_data['results'] = response.get('data', [])
        formatted_data['is_auth_plp'] = True
        formatted_data['pin_id'] = self.options.get('id')
        response['data'] = formatted_data

    def get(self):
        start_time_ms = time_utils.now_millis()
        request_data = {}
        pin_id = self.options.get('id')
        if not pin_id:
            stat_client.increment(
                'event.seo.pin_resource.no_pin_id', sample_rate=1)
            return self.response_error("Pin id is not provided")

        # Strip keywords from SEO pin id for pin lookup.
        is_seo_keyword_pin = ('--' in unicode(pin_id)) and seo_pin_id_regex.match(unicode(pin_id))
        if is_seo_keyword_pin:
            pin_url_keywords = pin_id.split('--', 1)[0]
            stripped_pin_id = pin_id.split('--', 1)[1]
            pin_id = stripped_pin_id if stripped_pin_id.isdigit() else pin_id

        # If in auth pin landing page experiment request pin landing page metadata
        group = self._auth_plp_refresh_experiment_gating() or ""
        if group.startswith('enabled') and not self.options.get('is_landing_page'):
            redirect_url = '/pin/%s/?lp=true' % pin_id
            if self.options.get('pure_react', False):
                return self.response_success({'redirect_url': redirect_url})
            else:
                self.context.redirect = redirect_url
                return self.response_success({})
        elif self.options.get('is_landing_page'):
            data = {
                'pin': pin_id,
                'guides_size': SEARCH_GUIDES_LIMIT,
                'allow_horizontal_guides': True,
            }
            response = self.request('/v3/auth-landing-page/pins/', data=data)
            if response.get('status') == APIStatus.SUCCESS and response.get('data'):
                self._auth_plp_format_data(response)
                return response
            else:
                self.options['bookmarks'] = []

        self._log_paid_acq_session_metric()

        if self.context.request_debug:
            # Debug dataset selector for visual search
            request_data['deb_simlist'] = self.context.request_debug.get('deb_simlist')

        response = self.request('/v3/pins/%s/' % pin_id, data=request_data)
        if response.get('status') != APIStatus.SUCCESS:
            # 301 redirect deleted Pin (404) to its canonical Pin
            if (response.get('http_status') != 404 or
                    not pin_page_regex.match(self.context.path)):
                return response
            response = self.request(
                '/v3/pins/%s/canonical_pin/' % pin_id, data=request_data, ignore_bookmark=True)
            if (response.get('status') != APIStatus.SUCCESS or
                    not (response.get('data') or {}).get('id')):
                return response
            pin_id = response['data']['id']
            if self.options.get('pure_react', False):
                response['data'] = {
                    'redirect_url': '/pin/%s/' % pin_id
                }
            else:
                self._redirect(pin_id)

        data = response['data']

        # Add show_personalize_field
        cm_cookie = self.context.cookies.get('_pinterest_cm')
        unauth_id = cookie_utils.get_unauth_id_via_cm(cm_cookie)
        self.show_personalize_field = False
        if unauth_id:
            resp = self.request('/v3/cookies/%s/interests/' % unauth_id, ignore_bookmark=True)
            if resp.get('status') == APIStatus.SUCCESS and resp.get('data'):
                self.show_personalize_field = True
        if response.get('data'):
            response['data']['show_personalize_field'] = self.show_personalize_field
            buyable_product = response.get('data').get('buyable_product')
            if buyable_product and \
                    not self.context.experiments.v2_in_group('web_commerce', WEB_ACCESS_GROUPS):
                response['data']['buyable_product'] = None

        if 'comments' in data:
            # Keep this in sync with pin_comments_resource.py.
            data['comments']['data'].reverse()

        self.context.app_interstitial_data = app_interstitial.get_pin_data(data)

        if (self.context.is_authenticated):
            return response

        # return early for "obfuscated" pin urls and set canonical_url
        if pin_id != data.get('id'):
            if not data.get('id'):
                return response

            exp_group = self.context.get_seo_experiment_group(
                'seo_canonicalize_obfuscated_pin_url',
                unique_id=data.get('image_signature'))

            if exp_group and exp_group.startswith('enabled'):
                # set canonical_url to the pin url for decoded pin
                self.context['canonical_url'] = '/pin/%s/' % data['id']

            return response

        # Fetch pin join data and visual descriptions.
        fetch_visual_descriptions = self.context.language in seo_utils.VISUAL_DESCRIPTION_LANGUAGES

        if fetch_visual_descriptions:
            request_params = {
                'pins': pin_id,
                'fields':
                    'pinjoin.seo_description,pinjoin.visual_annotation,' +
                    'pinjoin.canonical_pin(),' +
                    'pin.id,' + ','.join(UserResource.field_sets['unauth_thumb'])
            }

            if self.context.language == 'en':
                # why can't I use += here?
                request_params['fields'] = request_params['fields'] + ",pinjoin.visual_descriptions"
            else:
                request_params['fields'] = request_params['fields'] + ",pinjoin.i18n_visual_descriptions"

            (in_seo_signal_exp, seo_signal_exp_group) =\
                seo_signal_utils.is_enabled_in_seo_signal_exp(self.context)

            if in_seo_signal_exp:
                request_params['fields'] = request_params['fields'] + ",pinjoin.annotations"
                request_params['fields'] = request_params['fields'] + ",pinjoin.descriptions"

            pin_join_response = self.request(
                '/v3/pin_joins/',
                data=request_params,
                ignore_bookmark=True)

            if pin_join_response.get('status') != APIStatus.SUCCESS:
                return response
            pin_join = pin_join_response.get('data', {}).get(data['id'])
            if pin_join:
                data['pin_join'] = pin_join
                canonical_pin = pin_join.get('canonical_pin', {})
                if canonical_pin and canonical_pin.get('id') != pin_id and self.context.language == 'en':
                    self._set_canonical_url(canonical_pin)
                seo_signal_utils.set_pin_join_data(data, in_seo_signal_exp, seo_signal_exp_group)

            end_time_ms = time_utils.now_millis()
            opentsdb_client_v2.timing('denzel.resource.PinResource.get',
                                      end_time_ms - start_time_ms, sample_rate=0.1,
                                      tags=build_metric_tags(self.context))

        # Show url tags in the unauth pin's url if they exist.
        if data.get('url_tags') and self.context.language == 'en' and decider.decide_experiment('use_pin_keywords'):
            data['show_url_tags'] = True

            # 301 redirect pins without the keywords to the version with keywords,
            # and pins with the wrong keywords to the version with correct keywords.
            if not is_seo_keyword_pin or (pin_url_keywords and pin_url_keywords != data.get('url_tags')):
                canonical_pin_id = canonical_pin.get('id') if self.context.get('canonical_url') else pin_id
                self.context.redirect = '/pin/%s--%s/' % (data['url_tags'], canonical_pin_id)

        # TODO(cegbukichi): Remove when experiment is over.
        # Add the unauth pin to the profile interlinks experiment
        seo_utils.add_profile_interlinks_data(self, [data])

        return response

    def _get_canonical_og_url(self):
        pin_id = self.options['id']

        url_parse_result = urlparse.urlparse(self.context.current_url)
        if url_parse_result.netloc == CANONICAL_MAIN_DOMAIN:
            pin_join_response = self.request('/v3/pin_joins/',
                                             data={'pins': self.options['id'], 'fields': 'pinjoin.canonical_pin()'},
                                             ignore_bookmark=True)
            canonical_pin_id = data_structure_utils.safe_access(
                pin_join_response, "rsp['data']['{pin_id}']['canonical_pin']['id']".format(pin_id=self.options['id']))
            stat_client.increment('event.fbo.canonical_pin.%s' % 'found' if canonical_pin_id else 'missed',
                                  sample_rate=1)
            pin_id = canonical_pin_id if canonical_pin_id else pin_id
        return metatags.get_pin_url({'id': pin_id},
                                    main_url='{scheme}://{domain}'.format(scheme=url_parse_result.scheme,
                                                                          domain=url_parse_result.netloc))

    def _handle_fb_play_icon(self, data, overrides):
        pin_type = None
        if data.get('is_video'):
            pin_type = 'video'
        elif (data.get('embed') or {}).get('type') == 'gif':
            pin_type = 'gif'

        if pin_type:
            fb_thumbnail = data.get('fb_play_icon_thumbnail')
            if not fb_thumbnail:
                stat_client.increment('event.fbo.play_icon.%s.missing_thumbnail' % pin_type)
                kafka_event.log_as_json('fbo_misc_log', {'event_type': 'missing_thumbnail',
                                                         'image_signature': data.get('image_signature')})
            else:
                stat_client.increment('event.fbo.play_icon.%s.show_play_icon' % pin_type)
                overrides['og:image'] = fb_thumbnail

    def _get_overriding_metadata(self, data):
        overrides = {}

        # Special Facebook optimizations
        # 1. Canonicalize "og:url" to boost ranking of pins shared to Facebook.
        # 2. Overlay a "play video" icon to animated pins, i.e. gifs and videos, when shared to Facebook.
        if self.context.browser_name == 'FacebookBot':
            overrides['og:url'] = self._get_canonical_og_url()
            self._handle_fb_play_icon(data, overrides)

        return overrides

    def _get_page_metadata_pin(self):
        fields = [
            'board.name',
            'board.url',
            'pin.board()',
            'pin.description',
            'pin.embed',
            'pin.fb_play_icon_thumbnail',
            'pin.id',
            'pin.images[736x,600x315]',
            'pin.image_signature',
            'pin.is_video',
            'pin.like_count',
            'pin.link',
            'pin.pinner()',
            'pin.repin_count',
            'pin.title',
            'pin.url_tags',
            'pin.rich_metadata()',
            'user.full_name',
            'user.indexed',
            'user.twitter_url',
            'user.username',
        ]

        if not self.context.is_authenticated:
            fields += ['pin.pin_join()', 'pinjoin.visual_annotation']

        return self.request(
            '/v3/pins/%s/' % self.options['id'],
            data={'fields': ','.join(fields)}, ignore_bookmark=True)

    def _get_task_result(self, results, index):
        (exception, result) = results[index]
        if exception:
            raise exception
        return result

    def _get_hreflang_data(self, data):
        """Return a dict used to render the appropriate hreflang metatags on the page.

        If the pin falls into the SEO pin keyword url experiment, only render hreflangs for
        English locales since we currently only support English keywords.

        Otherwise, return an empty dictionary and allow webapp/context.py to generate
        hreflangs for all locales.
        """
        hreflang_data = {}
        in_pin_url_tags_exp = None
        if data.get('url_tags'):
            pin_url_tags_grp = self.context.activate_seo_or_unauth_experiment('pin_url_tags',
                                                                              unique_id=data.get('image_signature'))
            in_pin_url_tags_exp = pin_url_tags_grp and pin_url_tags_grp.startswith('enabled')

        if in_pin_url_tags_exp:
            for _, domain_info in country_domain_utils.get_hreflang_domain_configs().iteritems():
                if domain_info.get('locale').startswith('en'):
                    hreflang_data[domain_info.get('locale')] = self.context.path
            hreflang_data['en-US'] = self.context.path
        return hreflang_data

    def get_page_metadata(self):
        start_time_ms = time_utils.now_millis()

        pin_id = self.options.get('id')

        barrier = BarrierAll(abort_on_task_failure=False)
        barrier.add_task(self._get_page_metadata_pin)
        if not self.context.is_authenticated:
            barrier.add_task(self._is_banned_pin)
            barrier.add_task(metatag_keywords.get_related_keywords, self, pin_id=pin_id)

        results = barrier.wait(include_exception=True, timeout=20)

        result = self._get_task_result(results, 0)
        if result.get('status', APIStatus.SUCCESS) == APIStatus.SUCCESS:
            data = result['data']

            if not self.context.is_authenticated:
                result = self._get_task_result(results, 1)
                data['is_banned'] = result
                data['full_path'] = self.context['full_path']
                data['related_klps'] = self._get_task_result(results, 2).get('data', {})

            metadata_overrides = self._get_overriding_metadata(data)
            metadata = metatags.get_pin_metadata(self.context, data, overrides=metadata_overrides)
            metatags.log_page_title(self, metatags.PAGE_TYPE_PIN, metadata['title'], self.context['full_path'])

            if not self.context['is_amp']:
                metadata['links'] = \
                    [('amphtml', self.context.get_canonical_absolute_url().replace('/pin/', '/amp/pin/', 1))]
                metadata['hreflang_data'] = self._get_hreflang_data(data)

            end_time_ms = time_utils.now_millis()
            opentsdb_client_v2.timing('denzel.resource.PinResource.get_page_metadata',
                                      end_time_ms - start_time_ms, sample_rate=0.1,
                                      tags=build_metric_tags(self.context))
            return metadata

    def _is_banned_pin(self):
        # TODO(chris): This is slow and sloppy.  This should be a join on a pin so
        # that we don't have serialized API requests.
        response = self.request('/v3/pins/%s/spam_status/' % self.options.get('id'),
                                field_set_key='none', ignore_bookmark=True)
        return response.get('data', {}).get('is_banned') if response.get('status') == APIStatus.SUCCESS else False

    def _set_canonical_url(self, canonical_pin):
        canonical_pin_id = (canonical_pin or {}).get('id')
        if (re.match(r'^/pin/[0-9]+/.*$', self.context.full_path)
                and str(canonical_pin_id) not in self.context.full_path):
            self.context['canonical_url'] = '/pin/%s/' % canonical_pin_id

    def create(self):

        method = self.options.get('method', 'uploaded')
        if method == 'link':
            method = 'button_external'

        data = {
            'board_id': self.options.get('board_id'),
            'description': self.options.get('description'),
            'source_url': self.options.get('link', ''),
            'image_url': self.options.get('image_url'),
            'is_video': self.options.get('is_video'),
            'share_facebook': self.options.get('share_facebook'),
            'share_twitter': self.options.get('share_twitter'),
            'method': method,
            'guid': self.options.get('guid')
        }

        # Upload integrity monitoring (owned by partner experience)
        partner_upload_tags = self.options.get('upload_metric', None)
        if partner_upload_tags:
            # We're sending two, nearly duplicate events to help us transition
            # to a more generic metric name. TODO: khjertberg@ remove the extra
            # event when we have enough historic data in the new metric.
            if partner_upload_tags.get('source') == PARTNER_UPLOAD_SOURCE:
                opentsdb_client_v2.increment('adgrow.partner_image_upload.pin_resource',
                                             sample_rate=1,
                                             tags={'source': partner_upload_tags.get('source', 'unknown'),
                                                   'resource': 'python'})
            opentsdb_client_v2.increment('pin_create.image_upload.pin_resource',
                                         sample_rate=1,
                                         tags={'source': partner_upload_tags.get('source', 'unknown'),
                                               'resource': 'python'})

        if self.options.get('video_id'):
            data['video_id'] = self.options.get('video_id')

        if self.options.get('media_upload_id'):
            data['media_upload_id'] = self.options.get('media_upload_id')

        if self.options.get('image_base64'):
            data.pop('image_url', None)
            data['image_base64'] = self.options.get('image_base64')

        if self.options.get('color'):
            data.pop('image_url', None)
            data['color'] = self.options.get('color')

        if self.options.get('parent_csr_id'):
            data['parent_csr_id'] = self.options.get('parent_csr_id')

        response = self.request('/v3/pins/', data=data,
                                field_set_key='create_success',
                                method='PUT')

        # CSR creates are logged separately in PinCreate.js, as it's simpler to pass auxData there
        if response and response.get('status') == APIStatus.SUCCESS:
            if not self.options.get('is_csr') and response.get('data') and response.get('data').get('id'):
                self.context.event_log_info = EventLogInfo(EventType.PIN_CREATE, '').to_dict()
        return response

    @log_context(EventType.PIN_DELETE, object_id_str_key='id')
    @require_explicit_login
    def delete(self):
        data = {}
        return self.request('/v3/pins/%s/' % self.options['id'],
                            data=data, method='DELETE')

    @log_context(EventType.PIN_EDIT, object_id_str_key='id')
    @require_explicit_login
    def update(self):
        data = {}

        board_id = self.options.get('board_id')
        description = self.options.get('description')
        link = self.options.get('link')

        data['board_id'] = board_id
        data['description'] = description
        data['link'] = link

        return self.request('/v3/pins/%s/' % self.options['id'],
                            data=data, field_set_key='detailed', method='POST')
