import settings
from schemas.event_if.ttypes import ViewParameterType
from schemas.event_if.ttypes import ViewType
from schemas.logservice.ttypes import UpwtActionName
from webapp.denzel.router import Router

router = Router()
r = router.add_route
rexp = router.add_route_exp

r(r'^/follow/:username/*$', 'AutoFollow', {'username': '${username}'},
    require_authentication=True,
    login_parameters={'username': '${username}', 'auto_follow': 'true'})

r(r'^/follow/:username/:slug/*$', 'AutoFollow',
    {'username': '${username}', 'username_and_slug': '${username}/${slug}'},
    require_authentication=True,
    login_parameters={'username': '${username}', 'boardname': '${slug}', 'auto_follow': 'true'})

r(r'^/logout/', 'LogoutPage', {'next': '?{next}'},
    content_only=True,
    hide_interstitial=True)

# Public feeds
r(r'^/all/$', 'FeedPage',
    {'feed': 'everything'},
    resource={
        'name': 'CategoryResource',
        'options': {
            'category': 'everything',
        },
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_EVERYTHING,
    },
    perf_log=True,
    redirect='/categories/everything/')
r(r'^/all/:category/$', 'FeedPage',
    {'feed': '${category}', 'is_category': True},
    resource={
        'name': 'CategoryResource',
        'options': {
            'category': '${category}',
        },
    },
    log={
        'view_type': ViewType.FEED,
        'view_data': {
            'feed': '${category}',
            'is_category': True
        }},
    perf_log=True,
    redirect='/categories/${category}/')

# Conversations
r(r'^/conversation/:conversation_id/*$', 'HomePage',
    {
        'tab': 'following',
        'email_updated': '?{ues}',
        'allow_nux': '?{allow_nux}',
        'conversation_id': '${conversation_id}',
        'pin_id': '?{pin_id}',
        'auto_follow_interest': '?{auto_follow_interest}'
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_HOME
    },
    ios_deep_link='pinterest://conversation/${conversation_id}',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + 'conversation/${conversation_id}',
    upwt_action_name=UpwtActionName.HOME_FEED_RENDER)

# Promo stuff [Place Pins]
r(r'^/places/examples/$', '', redirect='/')


r(r'^/popular/$', 'FeedPage',
    {'feed': 'popular'},
    resource={
        'name': 'CategoryResource',
        'options': {
            'category': 'popular',
        },
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_POPULAR,
    },
    perf_log=True,
    redirect='/categories/popular/')

r(r'^/fresh/$', 'FeedPage',
    {'feed': 'fresh'},
    resource={
        'name': 'CategoryResource',
        'options': {
            'category': 'fresh',
        },
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_FRESH,
    },
    perf_log=True,
    redirect='/categories/fresh/')

r(r'^/gifts/$', 'FeedPage',
    {'feed': 'gifts', 'low_price': '?{low_price}', 'high_price': '?{high_price}'},
    resource={
        'name': 'CategoryResource',
        'options': {
            'category': 'gifts',
        },
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_GIFTS,
    },
    perf_log=True,
    redirect='/categories/gifts/')

r(r'^/videos/$', 'FeedPage',
    {'feed': 'videos'},
    resource={
        'name': 'CategoryResource',
        'options': {
            'category': 'videos',
        },
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_VIDEOS,
    },
    perf_log=True,
    redirect='/categories/videos/')

r(r'^/explore/$', '', redirect='/categories/')

# Keyword landing pages
_klp_react_basics_enabled_config = {
    'module': 'InterestFeedReactPage',
    'wrapper_name': 'InterestFeedReactPage',
    'options': {'interest': '${interest}', 'show_follow_memo': '?{auto_follow}'},
    'resource': {
        'name': 'InterestResource',
        'options': {
            'field_set_key': 'unauth_react',
            'interest': '${interest}',
            'no_gift_wrap': '?{no_gift_wrap}',
            'main_module_name': 'InterestFeedReactPage'
        }
    },
    'log': {
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_KLP,
        'view_data': {
            'interest': '${interest}',
        },
    },
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/explore/${interest}',
    'ios_deep_link': 'pinterest://explore/${interest}',
    'perf_log': True,
    'canonical_url': '/explore/${interest}/',
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.KLP_PAGE_LOAD}

# Explore page for auth
_explore_denzel = {
    'module': 'InterestFeedPage',
    'options': {'interest': '${interest}', 'show_follow_memo': '?{auto_follow}'},
    'resource': {
        'name': 'InterestResource',
        'options': {
            'interest': '${interest}',
            'no_gift_wrap': '?{no_gift_wrap}',
            'main_module_name': 'InterestFeedPage'
        }
    },
    'log': {
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_KLP,
        'view_data': {
            'interest': '${interest}',
        },
    },
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/explore/${interest}',
    'ios_deep_link': 'pinterest://explore/${interest}',
    'perf_log': True,
    'canonical_url': '/explore/${interest}/',
    'show_klp_bar': True,
    'upwt_action_name': UpwtActionName.KLP_PAGE_LOAD}

# Open unauth keyword landing page.
_klp_react_open_config = {
    'module': 'OpenInterestFeedReactPage',
    'wrapper_name': 'OpenInterestFeedReactPage',
    'options': {'interest': '${interest}', 'show_follow_memo': '?{auto_follow}'},
    'resource': {
        'name': 'InterestResource',
        'options': {
            'field_set_key': 'unauth_react',
            'interest': '${interest}',
            'no_gift_wrap': 'true',
            'main_module_name': 'OpenInterestFeedReactPage'
        }
    },
    'log': {
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_KLP,
        'view_data': {
            'interest': '${interest}',
        },
    },
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/explore/${interest}',
    'ios_deep_link': 'pinterest://explore/${interest}',
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'perf_log': True,
    'canonical_url': '/explore/${interest}/',
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.KLP_PAGE_LOAD}

# us open klp react page that can be open or closed
_open_closed_klp_react_enabled_config = {
    'module': 'OpenClosedInterestFeedReactPage',
    'wrapper_name': 'OpenClosedInterestFeedReactPage',
    'options': {'interest': '${interest}', 'show_follow_memo': '?{auto_follow}'},
    'resource': {
        'name': 'InterestResource',
        'options': {
            'field_set_key': 'unauth_react',
            'interest': '${interest}',
            'no_gift_wrap': 'true',
            'main_module_name': 'OpenClosedInterestFeedReactPage'
        }
    },
    'log': {
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_KLP,
        'view_data': {
            'interest': '${interest}',
        },
    },
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/explore/${interest}',
    'ios_deep_link': 'pinterest://explore/${interest}',
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'perf_log': True,
    'canonical_url': '/explore/${interest}/',
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.KLP_PAGE_LOAD}


# Testing extracting redirect behavior out of the resource
def _activate_redirect_exp(route_copy, url, params, context=None):
    """
    Within the explore unauth page, if we are in the `web_interests_redirect` experiment,
    return a new route and activate this unauth experiment.
    """
    if not context:
        return route_copy

    if context.is_bot.lower() == 'true':
        exp_group = context.activate_seo_or_unauth_experiment('web_interests_redirect')
        if exp_group in ('control', 'control_5'):
            return route_copy

    route_copy.extra_context.update({'redirect_handler': 'get_explore_redirect',
                                     'redirect_inputs': {'interest': '${interest}'},
                                     'klp_redirect_exp': True})
    return route_copy

# AMP KLP
_amp_klp_config = {
    'module': 'AMPUnauthInterestFeedPage',
    'options': {'interest': '${interest}', 'show_follow_memo': '?{auto_follow}'},
    'resource': {
        'name': 'PureReactKLPResource',
        'options': {
            'interest': '${interest}',
            'no_gift_wrap': '?{no_gift_wrap}',
            'main_module_name': 'AMPUnauthInterestFeedPage',
            'page_size': 50
        }
    },
    'log': {
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_KLP,
        'view_data': {
            'interest': '${interest}',
        },
    },
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/explore/${interest}',
    'is_amp': True,
    'ios_deep_link': 'pinterest://explore/${interest}',
    'perf_log': True,
    'canonical_url': '/explore/${interest}/',
}

# Routing for /explore/:interest is currently being determined by the us_open_umbrella_klp
# experiment config.
# All auth users are going to see the denzel version of this route.
rexp(r'^/explore/:interest/$', 'us_open_umbrella_klp', {
    'control': _klp_react_basics_enabled_config,
    'control5': _klp_react_basics_enabled_config,
    'ao_react': _klp_react_open_config,
    'forced_open': _klp_react_open_config,
    'forced_open5': _klp_react_open_config,
    'amp_control': _open_closed_klp_react_enabled_config,
    'amp_enabled': _amp_klp_config,
    'rollout': _open_closed_klp_react_enabled_config},
    default_config_auth=_explore_denzel,
    default_config_unauth=_klp_react_basics_enabled_config,
    exp_group_overwrite_unauth=True,
    config_filter=_activate_redirect_exp)

# AMP KLP
r(r'^/amp/explore/:interest/$', **_amp_klp_config)

# unauth open personalized feed
r(r'^/personalized_feed/$', 'OpenPersonalizedFeedPage',
    {
        'type': '?{type}',
        'topics': '?{topics}',
        'pins': '?{pins}'
    },
    log={
        'view_type': ViewType.FEED,
    },
    react_only=True,
    content_only=True,
    disable_css=True,
    enable_partial_bundle=True,
    perf_log=True)

# Topic feeds
r(r'^/topics/:interest/$', 'TopicFeedPage',
    {'interest': '${interest}', 'show_follow_memo': '?{auto_follow}'},
    redirect_unauth='/explore/${interest}/',
    resource={
        'name': 'TopicResource',
        'options': {
            'interest': '${interest}',
            'main_module_name': 'TopicFeedPage'
        }
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_INTEREST,
        'view_data': {
            'interest': '${interest}',
        },
    },
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/explore/${interest}',
    ios_deep_link='pinterest://explore/${interest}',
    perf_log=True,
    canonical_url='/topics/${interest}/',
    show_klp_bar=True)

# Explore Tab Article
explore_tab_article_config = {
    'module': 'UnauthExploreReactPage',
    'options': {
        'id': '${id}',
        'board_id': '?{board_id}',
        'interest_id': '?{interest_id}',
        'query': '?{query}',
        'image': '?{image}',
        'topic': '?{topic}'
    },
    'log': {
        'view_type': ViewType.ARTICLE
    },
    'hide_interstitial': True,
    'ios_deep_link': 'pinterest://discover_article/${id}/?is_deeplink=1',
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/discover/article/${id}',
    'content_only_if_unauth': True
}
r(r'^/discover/article/:id/$', **explore_tab_article_config)

# Explore tab feed
explore_tab_feed_config = {
    'module': 'ExploreTabContainer',
    'options': {
        'section_id': '${section_id}'
    },
    'log': {
        'view_type': ViewType.EXPLORE
    },
    'hide_interstitial': True,
    'ios_deep_link': 'pinterest://discover_topics/${section_id}',
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/discover/topics/${section_id}',
    'content_only_if_unauth': True
}
r(r'^/discover/topics/:section_id/$', **explore_tab_feed_config)

explore_tab_config = {
    'module': 'ExploreTabContainer',
    'log': {
        'view_type': ViewType.EXPLORE
    },
    'hide_interstitial': True,
    'ios_deep_link': 'pinterest://discover',
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/discover',
    'content_only_if_unauth': True
}
r(r'^/discover/$', **explore_tab_config)

# Search
search_page_noscope_config = {
    'module': 'SearchPage',
    'options': {
        'scope': 'pins',
        'query': '?{q}',
        'restrict': '?{restrict}',
        'constraint_string': '?{fc}',
        'auth_lp_type': '?{lp}',
        'plp_id': '?{pin}'
    },
    'resource': {
        'name': 'BaseSearchResource',
        'options': {'scope': 'pins', 'query': '?{q}'}},
    'log': {
        'view_type': ViewType.SEARCH,
        'view_parameter': ViewParameterType.SEARCH_PINS,
    },
    'perf_log': True,
    'ios_deep_link': 'pinterest://search/?q=?{q}',
    'android_deep_link': 'pinterest://search/?q=?{q}',
    'upwt_action_name': UpwtActionName.SEARCH_FEED_RENDER
}
r(r'^/search/$', **search_page_noscope_config)

search_page_config = {
    'module': 'SearchPage',
    'options': {
        'scope': '${scope}',
        'query': '?{q}',
        'restrict': '?{restrict}',
        'constraint_string': '?{fc}',
        'auth_lp_type': '?{lp}',
        'plp_id': '?{pin}'
    },
    'resource': {
        'name': 'BaseSearchResource',
        'options': {
            'scope': '${scope}',
            'query': '?{q}',
            'restrict': '?{restrict}',
            'constraint_string': '?{fc}',
            'auth_lp_type': '?{lp}',
            'pin': '?{pin}'
        }
    },
    'log': {
        'view_type': ViewType.SEARCH,
        'view_data': {
            'scope': '${scope}',
        },
    },
    'perf_log': True,
    'ios_deep_link': 'pinterest://search/${scope}/?q=?{q}',
    'android_deep_link': 'pinterest://search/?q=?{q}',
    'upwt_action_name': UpwtActionName.SEARCH_FEED_RENDER
}
r(r'^/search/:scope/$', **search_page_config)

r(r'^/search/boards/places/$', 'SearchPage',
    {'query': '?{q}', 'layout': 'places', 'scope': 'boards'},
    resource={
        'name': 'BaseSearchResource',
        'options': {
            'scope': 'boards',
            'query': '?{q}',
            'layout': 'places'
        }
    },
    log={
        'view_type': ViewType.SEARCH,
        'view_parameter': ViewParameterType.SEARCH_PLACE_BOARDS,
        'view_data': {
            'scope': 'boards',
        },
    },
    perf_log=True,
    upwt_action_name=UpwtActionName.SEARCH_FEED_RENDER)

r(r'^/recipes/:ingredient/$', 'RecipeFeedPage',
    {'ingredient': '${ingredient}'},
    resource={
        'name': 'RecipePagesResource',
        'options': {
            'scope': 'recipes',
            'query': '${ingredient}'
        }
    },
    log={
        'view_type': ViewType.EXPLORE_FEED,
        'view_data': {
            'ingredient': '${ingredient}',
        }
    })

# Offsite.  There's a URL in front of this route that transforms its parameters.
r(r'^/offsite/$', 'OffsitePage',
    options={'sanitized_url': '?{sanitized_url}', 'redirect_status': '?{redirect_status}',
             'offsite_message': '?{offsite_message}'},
    content_only=True)

# OAuth
r(r'^/oauth/$', 'OAuthPage', {'consumer_id': '?{consumer_id}',
                              'response_type': '?{response_type}',
                              'redirect_uri': '?{redirect_uri}',
                              'scope': '?{scope}',
                              'state': '?{state}'},
    resource={
        'name': 'OAuthAuthorizationResource',
        'options': {
            'consumer_id': '?{consumer_id}',
            'response_type': '?{response_type}',
            'redirect_uri': '?{redirect_uri}',
            'scope': '?{scope}',
            'state': '?{state}'
        }},
    content_only=True,
    hide_interstitial=True)

r(r'^/oauth/dialog/$', 'OAuthDialog', {'consumer_id': '?{consumer_id}',
                                       'response_type': '?{response_type}',
                                       'redirect_uri': '?{redirect_uri}',
                                       'scope': '?{scope}',
                                       'state': '?{state}'},
    require_authentication=True,
    content_only=True,
    hide_interstitial=True)

r(r'^/pw/:username/$', 'ResetPasswordPageReactWrapper',
    {'username': '${username}', 'expiration': '?{e}', 'token': '?{t}'},
    resource={
        'name': 'VerifyEmailTokenResource',
        'options': {
            'username': '${username}',
            'expiration': '?{e}',
            'token': '?{t}'}},
    log={
        'view_type': ViewType.SETTINGS,
        'view_parameter': ViewParameterType.USER_ACTIVITY},
    suppress_nags=True,
    hide_interstitial=True)

_image_feed_page_enabled_config = {
    'module': 'ImagesFeedPageReactWrapper',
    'wrapper_name': 'ImagesFeedPageReactWrapper',
    'url': '?{url}',
    'options': {
        'url': '?{url}'
    }
}

_image_feed_page_control_config = {
    'module': 'ImagesFeedPage',
    'wrapper_name': 'ImagesFeedPage',
    'url': '?{url}',
    'options': {
        'url': '?{url}'
    },
    'resource': {
        'name': 'FindPinImagesResource',
        'options': {
            'url': '?{url}',
            'include_imageless': True
        },
    }
}

rexp(r'^/pin/find/$', 'save_image_feed_page_react', {
    'enabled': _image_feed_page_enabled_config,
    'employees': _image_feed_page_enabled_config,
    'control': _image_feed_page_control_config})

r(r'^/website/confirm/link/', 'DomainVerifyByLink',
    {'domain': '?{domain}'})

# Domain Verify
r(r'^/website/confirm/$', 'DomainVerify',
    resource={'name': 'DomainVerifyResource'},
    require_authentication=True)

r(r'^/verify_website/$', 'HeroVerifyWebsite', {'username': 'me'},
    resource={'name': 'UserResource', 'options': {'username': 'me'}})

# email verification error
r(r'/email_verification_error/$', 'EmailVerificationError', {},
    hide_interstitial=True)

# Subdomains
r(r'^/pinterest-international/$', 'InternationalSubdomains',
  resource={'name': 'SubdomainResource'},
  redirect_auth='/')

# Password Reset
r(r'^/password/reset/', 'PasswordResetReactWrapper',
    suppress_nags=True,
    content_only_if_mobile=True,
    hide_interstitial=True,
    redirect_auth='/',
    log={
        'view_type': ViewType.SETTINGS,
        'view_parameter': ViewParameterType.USER_ACTIVITY,
    })

r(r'^/business/convert/$', 'BusinessAccountConvertReactWrapper',
    hide_interstitial=True,
    redirect_partner='/business/getstarted/',
    require_authentication=True)

r(r'^/business/create/$', 'BusinessAccountCreateReactWrapper',
    content_only=True,
    redirect_partner='/business/getstarted/',
    resource={'name': 'PartnerCreateInspiredWallResource'})

# Network Notification Story landing page
r(r'^/news/:id/$', 'NetworkStoryLandingPage',
    require_authentication=True,
    resource={
        'name': 'NetworkStoryResource',
        'options': {'story_id': '${id}'}
    },
    redirect_on_404='/?redirected=1')

r(r'^/news/type/:type/$', 'NetworkStoryLandingPage',
    require_authentication=True,
    resource={
        'name': 'NetworkStoryByTypeResource',
        'options': {'story_type': '${type}'}
    },
    redirect_on_404='/?redirected=1')

# TODO(03-07-2016) ryankuo): remove this after a few days
news_hub_redirect_config = {
    'redirect': '/news_hub/${id}/'
}
r(r'^/news-hub/:id/$', **news_hub_redirect_config)

news_hub_config = {
    'module': 'NewsHubLandingPage',
    'options': {
        'news_id': '${id}',
    },
    'require_authentication': True,
    'resource': {
        'name': 'NewsHubDetailsResource',
        'options': {'news_id': '${id}', 'page_size': 5}
    },
    'android_deep_link': 'pinterest://news_hub/${id}',
    'ios_deep_link': 'pinterest://news_hub/${id}',
    'redirect_on_404': '/?redirected=1'
}
r(r'^/news_hub/:id/$', **news_hub_config)

# Pin Closeup, Edit and Repin
_pin_react_basics_enabled_config = {
    'module': 'UnauthPinReactPage',
    'wrapper_name': 'UnauthPinReactPage',
    'options': {
        'show_reg': '?{show_reg}',
        'sender': '?{sender}',
        'ptrf': '?{ptrf}',
        'force_refresh': '?{force_refresh}'
    },
    'resource': {
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'unauth_react_pin',
        },
    },
    'log': {
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }
    },
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'android_deep_link': 'pinterest://pin/${id}',
    'ios_deep_link': 'pinterest://pin/${id}',
    'perf_log': True,
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.PIN_PAGE_LOAD}

_pin_react_open_config = {
    'module': 'UnauthOpenPinReactPage',
    'wrapper_name': 'UnauthOpenPinReactPage',
    'options': {
        'show_reg': '?{show_reg}',
        'sender': '?{sender}',
        'ptrf': '?{ptrf}',
        'force_refresh': '?{force_refresh}'
    },
    'resource': {
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed',
            'fetch_visual_search_objects': False,
            'ptrf': '?{ptrf}'
        },
    },
    'log': {
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }
    },
    'android_deep_link': 'pinterest://pin/${id}',
    'ios_deep_link': 'pinterest://pin/${id}',
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'perf_log': True,
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.PIN_PAGE_LOAD
}

# us open pin react page that can be open or closed
_pin_react_open_closed_config = {
    'module': 'UnauthOpenClosedPinReactPage',
    'wrapper_name': 'UnauthOpenClosedPinReactPage',
    'options': {
        'show_reg': '?{show_reg}',
        'sender': '?{sender}',
        'ptrf': '?{ptrf}',
        'force_refresh': '?{force_refresh}'
    },
    'resource': {
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed',
            'fetch_visual_search_objects': False,
            'ptrf': '?{ptrf}',
            'check_is_open': True
        },
    },
    'log': {
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }
    },
    'android_deep_link': 'pinterest://pin/${id}',
    'ios_deep_link': 'pinterest://pin/${id}',
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'perf_log': True,
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.PIN_PAGE_LOAD
}

_pin_closeup_react_config = {
    'module': 'ReactCloseupPageWrapper',
    'wrapper_name': 'ReactCloseupPageWrapper',
    'options': {
        'show_reg': '?{show_reg}',
        'sender': '?{sender}',
        'ptrf': '?{ptrf}',
        'force_refresh': '?{force_refresh}',
        'is_landing_page': '?{lp}',
        'conversation_id': '?{conversation_id}',
        'feedback': '?{fbr}',
        'pin_id': '${id}'
    },
    'require_authentication': True,
    'require_explicit_login': True,
    'upwt_action_name': UpwtActionName.PIN_PAGE_LOAD
}

_pin_denzel_config = {
    'module': 'Closeup',
    'options': {
        'show_reg': '?{show_reg}',
        'sender': '?{sender}',
        'ptrf': '?{ptrf}',
        'conversation_id': '?{conversation_id}',
        'feedback': '?{fbr}',
        'force_refresh': '?{force_refresh}'
    },
    'resource': {
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed',
            'fetch_visual_search_objects': True,
            'ptrf': '?{ptrf}'
        },
    },
    'log': {
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }
    },
    'android_deep_link': 'pinterest://pin/${id}',
    'ios_deep_link': 'pinterest://pin/${id}',
    'perf_log': True,
    'show_klp_bar': True,
    'upwt_action_name': UpwtActionName.PIN_PAGE_LOAD
}

_pin_closeup_samsung_camera_config = {
    'module': 'UnauthSamsungCameraPinPage',
    'wrapper_name': 'UnauthSamsungCameraPinPage',
    'options': {
        'session_id': '?{session_id}'
    },
    'resource': {
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'unauth_react_pin',
        },
    },
    'log': {
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }
    },
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'android_deep_link': 'pinterest://pin/${id}',
    'ios_deep_link': 'pinterest://pin/${id}',
    'perf_log': True,
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.PIN_PAGE_LOAD
}


# AMP PIN
_amp_pin_config = {
    'module': 'AMPUnauthPinPage',
    'options': {'id': '${id}'},
    'resource': {
        'name': 'AMPOriginalPinAndRelatedPinFeedResource',
        'options': {
            'pin': '${id}',
            'add_vase': True,
            'add_original_pin': True,
            'page_size': 50,
            'pins_only': True,
            'field_set_key': 'unauth_react'
        }
    },
    'log': {
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        },
    },
    'android_deep_link': 'pinterest://pin/${id}',
    'is_amp': True,
    'ios_deep_link': 'pinterest://pin/${id}',
    'perf_log': True,
    'canonical_url': '/pin/${id}/'
}

rexp(r'^/pin/:id/$', 'us_open_umbrella_pin', {
    # combined to allow the resource to control open/close decision
    'rollout': _pin_react_open_closed_config,
    'rollout_undecided': _pin_react_open_closed_config,
    'control': _pin_react_basics_enabled_config,
    'control5': _pin_react_basics_enabled_config,
    'forced_open': _pin_react_open_config,
    'forced_open5': _pin_react_open_config,
    'ao_react': _pin_react_open_config,
    'ao_denzel': _pin_denzel_config,
    'auth_react': _pin_closeup_react_config,
    'auth_react_control': _pin_denzel_config,
    'auth_react_enabled': _pin_closeup_react_config,
    'auth_react_closeup_exp_denzel_control': _pin_denzel_config,
    'auth_react_closeup_exp_denzel_control_no_gator_no_follow': _pin_denzel_config,
    'auth_react_closeup_exp_2_denzel_control_no_gator_no_follow': _pin_denzel_config,
    'auth_react_closeup_exp_3_denzel_control_no_gator_no_follow': _pin_denzel_config,
    'auth_react_closeup_exp_4_denzel_control_no_gator_no_follow': _pin_denzel_config,
    'auth_react_closeup_exp_react_enabled': _pin_closeup_react_config,
    'auth_react_closeup_exp_2_react_enabled': _pin_closeup_react_config,
    'auth_react_closeup_exp_3_react_enabled': _pin_closeup_react_config,
    'auth_react_closeup_exp_4_react_enabled': _pin_closeup_react_config,
    'auth_react_closeup_activity_feed': _pin_closeup_react_config,
    'closed_react': _pin_react_basics_enabled_config,
    'samsung_camera_pin_page': _pin_closeup_samsung_camera_config,
    'amp_control': _pin_react_open_closed_config,
    'amp_enabled': _amp_pin_config,
    'employees': _pin_react_basics_enabled_config},
    default_config_auth=_pin_denzel_config,
    default_config_unauth=_pin_react_basics_enabled_config,
    exp_group_overwrite_unauth=True
)

r(r'^/amp/pin/:id/$', **_amp_pin_config)

_pin_closeup_react_promote_config = {
    'module': 'ReactCloseupPageWrapper',
    'wrapper_name': 'ReactCloseupPageWrapper',
    'noindex': True,
    'options': {
        'pin_id': '${id}',
        'show_quick_promote': True,
    },
    'log': {
        'view_type': ViewType.PIN,
        'view_parameter': ViewParameterType.MODAL_CREATE_CAMPAIGN,
        'view_data': {
            'pin_id': '${id}',
        }
    },
    'require_authentication': True,
    'require_explicit_login': True
}

_pin_closeup_denzel_promote_config = {
    'module': 'Closeup',
    'noindex': True,
    'options': {
        'show_quick_promote': True,
    },
    'resource': {
        'name': 'PinResource',
        'options': {
            'id': '${id}',
        }
    },
    'log': {
        'view_type': ViewType.PIN,
        'view_parameter': ViewParameterType.MODAL_CREATE_CAMPAIGN,
        'view_data': {
            'pin_id': '${id}',
        }
    },
    'upwt_action_name': UpwtActionName.PIN_PAGE_LOAD
}

# This route opens the promote modal over closeup, and thus uses the same experiment
# Owened by advertiser growth
rexp(r'^/pin/:id/promote/$', 'us_open_umbrella_pin', {
    'auth_react': _pin_closeup_react_promote_config},
    default_config_auth=_pin_closeup_denzel_promote_config,
    default_config_unauth=_pin_react_basics_enabled_config
)

r(r'^/promotion_previews/:key/$', 'PromotedPinPreview',
    options={
    },
    resource={
        'name': 'SterlingPreviewResource',
        'options': {
            'key': '${key}',
            'field_set_key': 'grid_item',
            'grid_position': '?{grid_position}',
            'query': '?{query}',
            'view_type': '?{view_type}'
        },
    },
    content_only=True)

r(r'^/web-result/save/$', 'PinCreate',
    options={
        'action': 'create',
        'method': 'csr',
        'hide_pin_credits': True,
        'is_clone_for_repin': True,
        'render_existing_pin': True,
        'is_csr': True,
        'source_url': '?{iframeurl}',
        'show_explicit_share': False,
        'parent_csr_id': '?{parentcsrid}'
    },
    resource={
        'name': 'FakePinResource',
        'options': {
            'description': '?{description}',
            'image_url': '?{imageurl}',
            'link': '?{iframeurl}'}},
    require_authentication=True,
    content_only=True,
    log={
        'view_type': ViewType.SAVE,
        'view_parameter': ViewParameterType.PIN_CREATE,
        'view_data': {
            'csr_id': '?{parentcsrid}',
        }
    })

r(r'^/web-result/:id/$', 'Closeup',
    resource={
        'name': 'CSRResource',
        'options': {
            'id': '${id}'
        }},
    options={
        'is_csr': True,
    },
    log={
        'view_type': ViewType.PIN,
        'view_parameter': ViewParameterType.PIN_CLOSEUP_BODY,
        'view_data': {
            'pin_id': '${id}'
        }
    },
    upwt_action_name=UpwtActionName.PIN_PAGE_LOAD)

# Gator
r(r'^/pin/:id/activity/$', 'AggregatedActivityFeed',
    noindex=True,
    options={},
    resource={
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed'
        }
    },
    log={
        'view_type': ViewType.AGGREGATED_PIN_FEED
    })

r(r'^/pin/:id/activity/tried/$', 'ActivityFeedReactWrapper',
    {
        'tab': 'tried',
        'featured_did_it_ids': '?{featured_did_it_ids}',
    },
    sub_page='tried/',
    resource={
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed'
        }
    },
    noindex=True,
    ios_deep_link='pinterest://pin_activity/${id}/?featured_did_it_ids=?{featured_did_it_ids}',
    log={
        'view_type': ViewType.AGGREGATED_DID_IT_FEED
    })

r(r'^/pin/:id/activity/saved/$', 'AggregatedActivityFeed',
    {'tab': 'saved'},
    sub_page='saved/',
    resource={
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed'
        }
    },
    noindex=True,
    log={
        'view_type': ViewType.AGGREGATED_PIN_FEED
    })

r(r'^/pin/:id/edit/$', 'Closeup', {'show_edit': True},
    resource={'name': 'PinResource', 'options': {'id': '${id}', 'field_set_key': 'detailed'}},
    log={
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }},
    canonical_url='/pin/${id}/',
    ios_deep_link='pinterest://pin/${id}',
    android_deep_link='pinterest://pin/${id}',
    perf_log=True,
    require_explicit_login=True,
    show_klp_bar=True,
    upwt_action_name=UpwtActionName.PIN_PAGE_LOAD)

r(r'^/pin/:id/repin/$', 'Closeup',
    {'show_repin': True},
    resource={
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed',
            'fetch_visual_search_objects': True,
            'ptrf': '?{ptrf}'
        }
    },
    log={
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }},
    ios_deep_link='pinterest://repin/${id}',
    android_deep_link='pinterest://repin/${id}',
    perf_log=True,
    show_klp_bar=True,
    upwt_action_name=UpwtActionName.PIN_PAGE_LOAD)

r(r'^/pin/:id/repin/x/$', 'PinBookmarklet',
    content_only=True,
    require_authentication=True,
    options={
        'action': 'repin',
        'method': 'bookmarklet',
        'default_repin_board_id': '?{bid}',
        'pin_id': '${id}'},
    resource={
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'repin'
        },
    },
    ios_deep_link='pinterest://repin/${id}',
    android_deep_link='pinterest://repin/${id}',
    upwt_action_name=UpwtActionName.BOOKMARKLET_PAGE_LOAD)

r(r'^/pin/:id/comments/$', 'Closeup',
    options={'show_reg': '?{show_reg}', 'sender': '?{sender}', 'show_comments': True},
    resource={'name': 'PinResource', 'options': {'id': '${id}', 'field_set_key': 'detailed'}},
    log={
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }},
    ios_deep_link='pinterest://pin/${id}',
    android_deep_link='pinterest://pin/${id}',
    perf_log=True,
    show_klp_bar=True,
    upwt_action_name=UpwtActionName.PIN_PAGE_LOAD)

# Translations aren't working in this file since the options are
# being processed at rendering time (so in whichever language will
# trigger the first request.)
r(r'^/pin/:id/repins/$', 'RepinsLikesFeedPage', {
    'pin_id': '${id}', 'type': 'repins'},
    noindex=True,
    resource={
        'name': 'RepinFeedResource',
        'options': {'pin_id': '${id}', 'page_size': 50}})

r(r'^/pin/:id/likes/$', 'RepinsLikesFeedPage', {
    'pin_id': '${id}', 'type': 'likes'},
    noindex=True,
    resource={
        'name': 'PinLikesResource',
        'options': {'pin_id': '${id}', 'page_size': 50}})

# Flashlight
r(r'^/pin/:id/visual-search/$', 'FlashlightReactWrapper',
    options={
        'pin_id': '${id}',
        'variant_id': '?{variant_id}',
        'catalog_id': '?{catalog_id}',
        'x': '?{x}',
        'y': '?{y}',
        'w': '?{w}',
        'h': '?{h}',
        'animation': '?{animation}'
    })

# Merchant page
r(r'^/shop_pins/merchants/:merchant/$', 'MerchantPageReactWrapper',
    {},
    resource={
        'name': 'ShopMerchantResource',
        'options': {
            'merchant': '${merchant}'
        }
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.PIN_PRODUCT_MERCHANT
    })

# Checkout page
r(r'^/shop_pins/checkout/$', 'CheckoutPageReactWrapper',
    {},
    resource={
        'name': 'ShoppingBagsRecommendationsResource',
        'options': {
            'show_personal_recommendation': False,
            'saved_buyable_pins_limit': 16,
        }
    },
    log={
        'view_type': ViewType.CHECKOUT,
        'view_parameter': ViewParameterType.BUYABLE_BAG_LIST
    })

_pinbookmarklet_react_control_config = {
    'module': 'PinBookmarklet',
    'content_only': True,
    'require_authentication': True,
    'ios_deep_link': 'pinterest://add_pin/?method=' + '${method}' +
                     '&image_url=' + '?{media}' +
                     '&source_url=' + '?{url}' +
                     '&description=' + '?{description}',
    'options': {
        'image_url': '?{media}',
        'url': '?{url}',
        'guid': '?{guid}',
        'title': '?{title}',
        'description': '?{description}',
        'is_video': '?{is_video}',
        'is_from_external': 'true',
        'method': '${method}',
        'is_imageless': '?{pinFave}',
        'is_inline': '?{is_inline}',
        'color': '?{color}'
    },
    'log': {
        'view_type': ViewType.BOOKMARKLET,
        'view_parameter': ViewParameterType.PIN_CREATE_PINMARKLET,
        'view_data': {
            'method': '${method}',
            'guid': '?{guid}'
        }
    },
    'perf_log': True,
    'upwt_action_name': UpwtActionName.BOOKMARKLET_PAGE_LOAD
}

# redirect widget links to pin/create in unauth to the unauth homepage
_pinbookmarklet_unauth_config = {
    'module': 'UnauthHomeReactPage',
    'wrapper_name': 'UnauthHomeReactPage',
    'options': {},
    'resource': {
        'name': 'InspiredWallResource',
        'options': {},
    },
    'log': {
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_HOME
    },
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'android_deep_link': 'pinterest://',
    'ios_deep_link': 'pinterest://',
    'perf_log': True,
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.UNAUTH_HOME_PAGE_LOAD
}

_pinbookmarklet_react_enabled_config = _pinbookmarklet_react_control_config.copy()
_pinbookmarklet_react_enabled_config['module'] = 'PinBookmarkletReactWrapper'
_pinbookmarklet_react_enabled_config['wrapper_name'] = 'PinBookmarkletReactWrapper'
_pinbookmarklet_react_enabled_config['react_only'] = True
_pinbookmarklet_react_enabled_config['disable_css'] = True
_pinbookmarklet_react_enabled_config['enable_partial_bundle'] = True

# Pin Bookmarklet
# if you change the url, image_url, or description params,
# please update the ShowCSRSaveButton module as well
rexp(r'^/pin/create/:method/$', 'react_pin_bookmarklet_2', {
    # seperate bundle experiment
    'enabled':  _pinbookmarklet_react_enabled_config,
    'enabled_2':  _pinbookmarklet_react_enabled_config,
    'employees': _pinbookmarklet_react_enabled_config,
    'control':  _pinbookmarklet_react_control_config,
    'control_2':  _pinbookmarklet_react_control_config},
    default_config_unauth=_pinbookmarklet_unauth_config,
)

# Landing page for a sent Pin
r(r'^/pin/:id/sent/$', 'SentPin',
    options={
        'show_reg': '?{show_reg}',
        'sender_id': '?{sender}',
        'conversation_id': '?{conversation}',
        'conversation_user_id': '?{user_id}',
        'conversation_obfuscated_data': '?{od}',
        'sent_pin_variant': '?{spe}',
    },
    resource={
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed'
        }},
    log={
        'view_type': ViewType.PIN,
        'view_data': {
            'pin_id': '${id}',
        }},
    ios_deep_link='pinterest://pin/${id}',
    android_deep_link='pinterest://pin/${id}',
    hide_interstitial=True,
    briofy=True,
    noindex=True,
    perf_log=True,
    hide_banner=True,
    show_klp_bar=True)


# User
user_settings_config = {
    'module': 'UserSettingsPageReactWrapper',
    'resource': {
        'name': 'UserSettingsResource'
    },
    'require_authentication': True,
    'require_explicit_login': True,
    'log': {
        'view_type': ViewType.SETTINGS
    },
    'ios_deep_link': 'pinterest://settings/',
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/settings/'
}
r(r'^/settings/$', **user_settings_config)

# After uninstalling the browser extension
r(r'^/settings/extension/uninstall/$', 'BrowserExtensionUninstallPage', {})


# Support unsubscribing from one or all email via a protected signed action paged.
r(r'^/email/subscription/$', 'SignedEmailUnsubscribePage',
    options={
        'confirmed': '?{confirmed}',
        'feedback': '?{feedback}'
    },
    resource={
        'name': 'SignedEmailSubscriptionResource',
        'options': {
            'user_id': '?{user_id}',
            'od': '?{od}'}},
    suppress_nags=True,
    suppress_js_nag=True,
    suppress_nag_download=True,
    hide_interstitial=True)

# Support editing all email settings via a protected signed action page.
r(r'^/email/settings/$', 'SignedEmailSettingsPage', {},
    content_only=True,
    resource={
        'name': 'SignedEmailSettingsResource',
        'options': {
            'user_id': '?{user_id}',
            'od': '?{od}'}},
    suppress_nags=True, suppress_js_nag=True, suppress_nag_download=True)


def _activate_web_react_user_follow_redirect(route_copy, url, params, context=None):
    if not context:
        return route_copy

    group = context.experiments.v2_activate_experiment('web_react_user_follow')
    if group in ['enabled_redirect2', 'enabled_redirect', 'employees']:
        url = url.replace('/follow/', '/')
        context.redirect = url

    return route_copy

_web_react_user_follow_config = {
    'module': 'UserProfileFollowReactWrapper',
    'content_only': True,
    'resource': {
        'name': 'UserResource',
        'options': {
            'username': '${username}',
            'field_set_key': 'detailed'
        }
    },
    'sub_page': 'pins/follow/',
    'ios_deep_link': 'pinterest://user/${username}?follow=1',
    'android_deep_link': 'pinterest://user/${username}?follow=1',
}

_web_react_user_follow_control_config = {
    'module': 'UserProfileFollow',
    'content_only': True,
    'resource': {
        'name': 'UserResource',
        'options': {
            'username': '${username}',
            'field_set_key': 'detailed'
        }
    },
    'sub_page': 'pins/follow/',
    'ios_deep_link': 'pinterest://user/${username}?follow=1',
    'android_deep_link': 'pinterest://user/${username}?follow=1',
}

# Profile Follow Page
# go ABOVE the pinpicks feature, otherwise the `pinpicks` username won't get detected
rexp(r'^/:username/pins/follow/$', 'web_react_user_follow', {
    'control': _web_react_user_follow_control_config,
    'control2': _web_react_user_follow_control_config,
    'enabled': _web_react_user_follow_config,
    'employees': _web_react_user_follow_config},
    config_filter=_activate_web_react_user_follow_redirect)


def _activate_web_react_board_follow_redirect(route_copy, url, params, context=None):
    if not context:
        return route_copy

    group = context.experiments.v2_activate_experiment('web_react_board_follow')
    if group in ['enabled_redirect', 'employees']:
        url = url.replace('/follow/', '/')
        context.redirect = url

    return route_copy

# Board Follow Page
r(r'^/:username/:slug/follow/$', 'UserBoardFollow',
    content_only=True,
    resource={
        'name': 'BoardResource',
        'options': {
            'username': '${username}',
            'slug': '${slug}',
            'field_set_key': 'detailed',
        }
    },
    board_sub_page='follow/',
    ios_deep_link='pinterest://board/${username}/${slug}?follow=1',
    android_deep_link='pinterest://board/${username}/${slug}?follow=1',
    config_filter=_activate_web_react_board_follow_redirect)

# pin picks
r(r'^/pinpicks/:country/:pinpick/$', 'PinPicksDetail',
    resource={
        'name': 'PinPicksResource',
        'options': {'pinpickname': '${pinpick}', 'country': '${country}'}
    },
    log={
        'view_type': ViewType.PINPICKS,
        'view_data': {
            'country': '${country}',
            'pinpickname': '${pinpick}'
        }},
    canonical_url='/pinpicks/${country}/${pinpick}/',
    ios_deep_link='pinterest://pinpicks/${country}/${pinpick}/',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/pinpicks/${country}/${pinpick}/')

# mobile landing page
r(r'^/mobile/$', 'MobileLandingPage',
    {'device': 'Mobile'},
    resource={
        'name': 'MobileLandingResource',
        'options': {'device': 'Mobile'},
    },
    content_only=True)

r(r'^/android/$', 'MobileLandingPage',
    {'platform': 'android', 'device': 'Android'},
    resource={
        'name': 'MobileLandingResource',
        'options': {'platform': 'android', 'device': 'Android'},
    },
    content_only=True)

r(r'^/ios/$', 'MobileLandingPage',
    {'platform': 'iOS', 'device': 'iOS'},
    resource={
        'name': 'MobileLandingResource',
        'options': {'platform': 'iOS', 'device': 'iOS'},
    },
    content_only=True)

r(r'^/iphone/$', 'MobileLandingPage',
    {'platform': 'iOS', 'device': 'iPhone'},
    resource={
        'name': 'MobileLandingResource',
        'options': {'platform': 'iOS', 'device': 'iPhone'},
    },
    content_only=True)

r(r'^/ipad/$', 'MobileLandingPage',
    {'platform': 'iOS', 'device': 'iPad'},
    resource={
        'name': 'MobileLandingResource',
        'options': {'platform': 'iOS', 'device': 'iPad'},
    },
    content_only=True)

r(r'^/tablet/$', 'MobileLandingPage',
    {'device': 'Tablet'},
    resource={
        'name': 'MobileLandingResource',
        'options': {'device': 'Tablet'},
    },
    content_only=True)

# Support disassociating email addresses from accounts via a protected action page.
r(r'^/email/remove/$', 'SignedEmailDisassociatePage', {},
    resource={
        'name': 'SignedEmailAssociationResource',
        'options': {
            'user_id': '?{user_id}',
            'od': '?{od}'}},
    suppress_nags=True, suppress_js_nag=True, suppress_nag_download=True)

# Editorial landing pages
r(r'^/editorial/:locale/:url_name/$', '',
    redirect='/explore/${url_name}/')

# Pinfluencer opt out confirmation page
r(r'^/pinfluencer/opted_out/$', 'PinfluencerOptOutConfirmationPage', {},
    suppress_nags=True, suppress_js_nag=True, suppress_nag_download=True)

# Home
_homepage_react_basics_enabled_config = {
    'module': 'UnauthHomeReactPage',
    'wrapper_name': 'UnauthHomeReactPage',
    'options': {
        'logged_out': '?{logged_out}',
        'show_error': '?{show_error}'
    },
    'resource': {
        'name': 'InspiredWallResource',
        'options': {
            #
        },
    },
    'log': {
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_HOME
    },
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'android_deep_link': 'pinterest://',
    'ios_deep_link': 'pinterest://',
    'perf_log': True,
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.UNAUTH_HOME_PAGE_LOAD
}

rexp(r'^/$', 'home_react_basics', {
    'enabled': _homepage_react_basics_enabled_config,
    'employees': _homepage_react_basics_enabled_config,
    'control': {
        'module': 'HomePage',
        'options': {
            'tab': 'following',
            'email_updated': '?{ues}',
            'allow_nux': '?{allow_nux}',
            'auto_follow_interest': '?{auto_follow_interest}',
            'prev': '?{prev}',
            'fb_ad': '?{fb_ad}',
            'cmp': '?{cmp}',
            'logged_out': '?{logged_out}',
            'show_error': '?{show_error}'
        },
        'log': {
            'view_type': ViewType.FEED,
            'view_parameter': ViewParameterType.FEED_HOME
        },
        'ios_deep_link': 'pinterest://feed/home',
        'android_deep_link': 'pinterest://',
        'content_only_if_unauth': True,
        'allow_nux': True,
        'is_home_page': True,
        'upwt_action_name': UpwtActionName.HOME_FEED_RENDER
    },
})

r(r'^/notifications/$', 'HomePage', {'tab': 'following', 'email_updated': '?{ues}', 'allow_nux': '?{allow_nux}',
                                     'auto_follow_interest': '?{auto_follow_interest}', 'prev': '?{prev}',
                                     'fb_ad': '?{fb_ad}', 'cmp': '?{cmp}', 'logged_out': '?{logged_out}',
                                     'notifications_open': True},
    log={'view_type': ViewType.FEED,
         'view_parameter': ViewParameterType.FEED_HOME},
    ios_deep_link='pinterest://notifications',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/notifications',
    content_only_if_unauth=True,
    allow_nux=True,
    is_home_page=True,
    upwt_action_name=UpwtActionName.HOME_FEED_RENDER)

r(r'^/source/:domain/$', 'DomainFeedPageReactWrapper',
    wrapper_name='DomainFeedPageReactWrapper',
    domain='${domain}',
    options={
        'domain': '${domain}'
    },
    resource={
        'name': 'DomainResource',
        'options': {
            'field_set_key': 'access',
            'domain': '${domain}'
        }
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_DOMAIN,
    })

# Invite Landing
r(r'^/invited/$', 'InviteLanding', {'inviter_user_id': '?{inviter_user_id}', 'invite_code': '?{invite_code}',
                                    'invite_type': '?{invite_type}'},
    content_only=True)

r(r'^/login/$',
    'UnauthLoginReactWrapper',
    wrapper_name='UnauthLoginReactWrapper',
    options={'next': '?{next}', 'auto_follow': '?{auto_follow}', 'prev': '?{prev}'},
    log={
        'view_type': ViewType.LOGIN
    },
    react_only=True,
    android_deep_link='pinterest://feed/home',
    ios_deep_link='pinterest://',
    disable_css=True,
    content_only=True,
    perf_log=True,
    enable_partial_bundle=True,
    upwt_action_name=UpwtActionName.UNAUTH_HOME_PAGE_LOAD)

r(r'^/login/reset/$', 'PasswordResetOneClick',
    {'username_or_email': '?{username_or_email}'},
    content_only=True,
    hide_interstitial=True)

r(r'^/join/signup/', '',
    redirect='/',
    hide_interstitial=True)

r(r'^/signup/', '',
    redirect='/',
    hide_interstitial=True)

r(r'^/join/register/', 'UnauthHomePage',
    {'register': True, 'wallClass': 'whiteWall', 'next': '?{next}'},
    resource={
        'name': 'InspiredWallResource',
        'options': {'override_story': 'register'}
    },
    content_only=True,
    hide_interstitial=True,
    upwt_action_name=UpwtActionName.UNAUTH_HOME_PAGE_LOAD)

r(r'^/join/.*$', 'UnauthHomePage',
    {'invite_follow_user': '?{username}', 'invite_follow_board': '?{boardname}', 'next': '?{next}',
     'auto_follow_interest': '?{auto_follow_interest}', 'prev': '?{prev}', 'wallClass': 'whiteWall', 'register': True},
    resource={
        'name': 'InspiredWallResource',
        'options': {'override_story': 'register'}
    },
    content_only=True,
    hide_interstitial=True,
    upwt_action_name=UpwtActionName.UNAUTH_HOME_PAGE_LOAD)

r(r'^/join/register/:network/', 'UserRegisterPage',
    {'network': '${network}', 'next': '?{next}', 'auto_follow_interest': '?{auto_follow_interest}', 'prev': '?{prev}'},
    content_only=True,
    hide_interstitial=True)

r(r'^/restricted/:reason/', 'UserRegisterRestricted',
    {'reason': '${reason}'},
    content_only=True,
    hide_interstitial=True)

# Categories
r(r'^/categories/$', 'CategoriesPage', {},
    resource={
        'name': 'CategoriesResource',
        'options': {
            'field_set_key': 'default',
            'category_types': 'main,non_board',
            'browsable': 'true'
        }},
    ios_deep_link='pinterest://search/',
    android_deep_link='pinterest://categories/',
    log={'view_type': ViewType.CATEGORY_GRID})

r(r'^/categories/:category/$', 'FeedPage', {
    'feed': '${category}', 'is_category': True, 'low_price': '?{low_price}', 'high_price': '?{high_price}'},
    resource={
        'name': 'CategoryResource',
        'options': {
            'category': '${category}',
        }, },
    ios_deep_link='pinterest://categories/${category}',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/categories/${category}',
    log={
        'view_type': ViewType.FEED,
        'view_data': {
            'feed': '${category}',
            'is_category': True
        }},
    perf_log=True)

# Errors
r(r'/csrf_error/$', 'CsrfErrorPage', {},
    hide_interstitial=True)
r(r'/oauth_error/$', 'OAuthErrorPage', {'error_message': '?{error_message}'},
    content_only=True,
    hide_interstitial=True)

# Trademark
r(r'^/about/trademark/form/$', 'TrademarkFormSelector',
    hide_interstitial=True)
r(r'^/about/trademark/form/:claim_type/$', 'TrademarkForm',
    {'claim_type': '${claim_type}'},
    hide_interstitial=True)

r(r'^/about/copyright/dmca-pin/web-result/:id', 'TakedownForm',
  options={'view_type': 'dmcapin', 'initial_value': settings.CANONICAL_MAIN_URL + '/web-result/' + '${id}'},
  hide_interstitial=True)
r(r'^/about/copyright/dmca-pin/pin/:id', 'TakedownForm',
  options={'view_type': 'dmcapin', 'initial_value': settings.CANONICAL_MAIN_URL + '/pin/' + '${id}'},
  hide_interstitial=True)
r(r'^/about/copyright/dmca-pin/', 'TakedownForm',
  options={'view_type': 'dmcapin'},
  hide_interstitial=True)

# Appeal
r(r'^/about/appeal/form/', 'AppealForm',
    options={},
    content_only=True, hide_interstitial=True)
r(r'^/appeal/submitted/$', 'AppealConfirmationPage', {},
    content_only=True, suppress_nags=True, suppress_js_nag=True, suppress_nag_download=True)

# Auth
r(r'^/loggedout/getapp/', 'LogoutAppUpsell', {'username': '?{username}'},
  content_only=True,
  hide_interstitial=True)

# Search recent pins
r(r'^/search/pins/recent/$', 'SearchPage',
    {'query': '?{q}', 'boost': 'recent_week', 'scope': 'pins'},
    resource={
        'name': 'BaseSearchResource',
        'options': {
            'scope': 'pins',
            'query': '?{q}',
            'boost': 'recent_week'
        }},
    log={
        'view_type': ViewType.SEARCH,
        'view_parameter': ViewParameterType.SEARCH_PINS,
    },
    perf_log=True,
    upwt_action_name=UpwtActionName.SEARCH_FEED_RENDER)

# Snackbox
r(r'^/dynamic-collection/:id/$', 'SnackboxResults',
    resource={
        'name': 'PinResource',
        'options': {
            'id': '${id}',
            'field_set_key': 'detailed',
        }
    })

# User
# "/board/create/"" is somehow linked to from email even though no email
# templates contain "/board/create/".  Talk to jennlee@
# before attempting to remove this route.
r(r'^/board/create/', 'UserProfilePage',
    {
        'tab': 'boards',
        'board_create': '1'
    },
    resource={
        'name': 'UserResource',
        'options': {
            'username': 'me'
        }
    },
    perf_log=True,
    upwt_action_name=UpwtActionName.USER_PAGE_LOAD)

user_profile_config = {
    'module': 'UserProfilePage',
    'options': {
        'tab': 'boards',
        'show_follow_memo': '?{auto_follow}',
        'show_redirected_memo': '?{redirected}'
    },
    'resource': {
        'name': 'UserResource',
        'options': {
            'username': '${username}', 'invite_code': '?{invite_code}'
        }
    },
    'ios_deep_link': 'pinterest://user/${username}',
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/${username}',
    'canonical_url': '/${username}/',
    'log': {
        'view_type': ViewType.USER,
        'view_parameter': ViewParameterType.USER_BOARDS,
    },
    'perf_log': True,
    'upwt_action_name': UpwtActionName.USER_PAGE_LOAD
}
r(r'^/:username/$', **user_profile_config)

user_boards_config = {
    'module': 'UserProfilePage',
    'options': {'tab': 'boards'},
    'resource': {
        'name': 'UserResource',
        'options': {
            'username': '${username}'
        }
    },
    'ios_deep_link': 'pinterest://user/${username}',
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/${username}',
    'log': {
        'view_type': ViewType.USER,
        'view_parameter': ViewParameterType.USER_BOARDS,
    },
    'perf_log': True,
    'upwt_action_name': UpwtActionName.USER_PAGE_LOAD
}
r(r'^/:username/boards/$', **user_boards_config)

user_pins_config = {
    'module': 'UserProfilePage',
    'options': {'tab': 'pins'},
    'sub_page': 'pins/',
    'resource': {
        'name': 'UserResource',
        'options': {
            'username': '${username}'
        }
    },
    'ios_deep_link': 'pinterest://user/${username}',
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/${username}',
    'log': {
        'view_type': ViewType.USER,
        'view_parameter': ViewParameterType.USER_PINS,
    },
    'perf_log': True,
    'upwt_action_name': UpwtActionName.USER_PAGE_LOAD
}
r(r'^/:username/pins/$', **user_pins_config)

r(r'^/:username/likes/$', 'UserProfilePage',
    {'tab': 'likes'},
    sub_page='likes/',
    resource={'name': 'UserResource', 'options': {'username': '${username}'}},
    ios_deep_link='pinterest://user/${username}',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/${username}',
    noindex=True,
    log={
        'view_type': ViewType.USER,
        'view_parameter': ViewParameterType.USER_LIKES,
    },
    perf_log=True,
    upwt_action_name=UpwtActionName.USER_PAGE_LOAD)

user_tried_config = {
    'module': 'UserProfilePage',
    'options': {'tab': 'tried'},
    'sub_page': 'tried/',
    'resource': {
        'name': 'UserResource',
        'options': {
            'username': '${username}'
        }
    },
    'ios_deep_link': 'pinterest://user/${username}',
    'android_deep_link': 'pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/${username}',
    'log': {
        'view_type': ViewType.USER,
        'view_parameter': ViewParameterType.USER_DID_IT,
    },
    'perf_log': True,
    'upwt_action_name': UpwtActionName.USER_PAGE_LOAD
}
r(r'^/:username/tried/$', **user_tried_config)

r(r'^/:username/liked-by/$', 'UserProfilePage',
    {'tab': 'likedby'},
    sub_page='liked-by/',
    resource={'name': 'UserResource', 'options': {'username': '${username}'}},
    ios_deep_link='pinterest://user/${username}',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/${username}',
    noindex=True,
    log={
        'view_type': ViewType.USER,
        'view_parameter': ViewParameterType.USER_FOLLOWERS,
    },
    perf_log=True,
    upwt_action_name=UpwtActionName.USER_PAGE_LOAD)

r(r'^/:username/followers/$', 'FollowersPageReactWrapper',
    sub_page='followers/',
    resource={'name': 'UserResource', 'options': {'username': '${username}'}},
    ios_deep_link='pinterest://user/${username}',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/${username}',
    noindex=True,
    log={
        'view_type': ViewType.USER,
        'view_parameter': ViewParameterType.USER_FOLLOWERS,
    },
    perf_log=True,
    upwt_action_name=UpwtActionName.FOLLOWERS_PAGE_LOAD)

r(r'^/:username/following/$', 'FollowingPageReactWrapper',
    sub_page='following/',
    resource={'name': 'UserResource', 'options': {'username': '${username}'}},
    ios_deep_link='pinterest://user/${username}',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/${username}',
    noindex=True,
    log={
        'view_type': ViewType.USER,
        'view_parameter': ViewParameterType.USER_FOLLOWING,
    },
    perf_log=True,
    upwt_action_name=UpwtActionName.FOLLOWING_PAGE_LOAD)

r(r'^/showcase/settings/$', 'ShowcaseSettingsWrapper',
    {
        'require_authentication': True,
        'require_explicit_login': True,
    },
    noindex=True)

# shop space
r(r'^/shop_space/$', '',
    redirect='/shop_pins/shop_space/',
    ios_deep_link='pinterest://shop_space/',
    android_deep_link='pinterest://shop_space/')

# shop space
r(r'^/shop_pins/shop_space/$', 'ShopSpace',
    {},
    resource={
        'name': 'ShopSpaceResource'
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_SHOP_SPACE,
    })

# order history page
r(r'^/pin_shop/order_history/$', 'OrderHistory',
    {})

# Board Unauth React
_board_unauth_react_config = {
    'module': 'UnauthBoardReactPage',
    'wrapper_name': 'UnauthBoardReactPage',
    'options': {
        'show_follow_memo': '?{auto_follow}',
        'inviter_user_id': '?{inviter_user_id}',
        'invite_code': '?{invite_code}',
        'board_invite_code': '?{board_invite_code}',
        'board_collab_inviter': '?{board_collab_inviter}',
        'slug': '${slug}',
        'invite_type': '?{invite_type}',
        'ptrf': '?{ptrf}'
    },
    'resource': {
        'name': 'BoardResource',
        'options': {
            'username': '${username}',
            'slug': '${slug}',
            'field_set_key': 'detailed',
            'main_module_name': 'UnauthBoardReactPage',
        }
    },
    'log': {
        'view_type': ViewType.BOARD,
        'view_data': {
            'username': '${username}',
        }
    },
    'react_only': True,
    'disable_css': True,
    'content_only': True,
    'android_deep_link': 'pinterest://board/${username}/${slug}',
    'ios_deep_link': 'pinterest://board/${username}/${slug}',
    'redirect_on_404': '/${username}/?redirected=1',
    'perf_log': True,
    'enable_partial_bundle': True,
    'upwt_action_name': UpwtActionName.BOARD_PAGE_LOAD}

# Board Unauth Open React
_unauth_open_board_react_enabled_config = {
    'module': 'UnauthOpenBoardReactPage',
    'wrapper_name': 'UnauthOpenBoardReactPage',
    'options': {
        'show_follow_memo': '?{auto_follow}',
        'inviter_user_id': '?{inviter_user_id}',
        'invite_code': '?{invite_code}',
        'board_invite_code': '?{board_invite_code}',
        'board_collab_inviter': '?{board_collab_inviter}',
        'slug': '${slug}',
        'invite_type': '?{invite_type}',
        'ptrf': '?{ptrf}'
    },
    'resource': {
        'name': 'BoardResource',
        'options': {
            'username': '${username}',
            'slug': '${slug}',
            'field_set_key': 'detailed',
            'main_module_name': 'UnauthOpenBoardReactPage'
        }
    },
    'log': {
        'view_type': ViewType.BOARD,
        'view_data': {
            'username': '${username}',
        }
    },
    'android_deep_link': 'pinterest://board/${username}/${slug}',
    'ios_deep_link': 'pinterest://board/${username}/${slug}',
    'content_only': True,
    'disable_css': True,
    'enable_partial_bundle': True,
    'perf_log': True,
    'react_only': True,
    'upwt_action_name': UpwtActionName.BOARD_PAGE_LOAD}

# Board Unauth Open or Closed React
_board_unauth_open_closed_react_config = {
    'module': 'UnauthOpenClosedBoardReactPage',
    'wrapper_name': 'UnauthOpenClosedBoardReactPage',
    'options': {
        'show_follow_memo': '?{auto_follow}',
        'inviter_user_id': '?{inviter_user_id}',
        'invite_code': '?{invite_code}',
        'board_invite_code': '?{board_invite_code}',
        'board_collab_inviter': '?{board_collab_inviter}',
        'slug': '${slug}',
        'invite_type': '?{invite_type}',
        'ptrf': '?{ptrf}'
    },
    'resource': {
        'name': 'BoardResource',
        'options': {
            'username': '${username}',
            'slug': '${slug}',
            'field_set_key': 'detailed',
            'main_module_name': 'UnauthOpenClosedBoardReactPage'
        }
    },
    'log': {
        'view_type': ViewType.BOARD,
        'view_data': {
            'username': '${username}',
        }
    },
    'android_deep_link': 'pinterest://board/${username}/${slug}',
    'ios_deep_link': 'pinterest://board/${username}/${slug}',
    'content_only': True,
    'disable_css': True,
    'enable_partial_bundle': True,
    'perf_log': True,
    'react_only': True,
    'upwt_action_name': UpwtActionName.BOARD_PAGE_LOAD}

# Board Denzel
_board_denzel_config = {
    'module': 'BoardPageWrapper',
    'options': {
        'show_follow_memo': '?{auto_follow}',
        'inviter_user_id': '?{inviter_user_id}',
        'invite_code': '?{invite_code}',
        'board_invite_code': '?{board_invite_code}',
        'board_collab_inviter': '?{board_collab_inviter}',
        'slug': '${slug}',
        'invite_type': '?{invite_type}',
        'ptrf': '?{ptrf}',
        'is_landing_page': '?{lp}'
    },
    'resource': {
        'name': 'BoardResource',
        'options': {
            'is_landing_page': '?{lp}',
            'username': '${username}',
            'slug': '${slug}',
            'field_set_key': 'detailed',
            'main_module_name': 'BoardPageWrapper',
        }
    },
    'log': {
        'view_type': ViewType.BOARD,
        'view_data': {
            'username': '${username}',
        }
    },
    'android_deep_link': 'pinterest://board/${username}/${slug}',
    'ios_deep_link': 'pinterest://board/${username}/${slug}',
    'redirect_on_404': '/${username}/?redirected=1',
    'perf_log': True,
    'show_klp_bar': True,
    'upwt_action_name': UpwtActionName.BOARD_PAGE_LOAD
}

rexp(r'^/:username/:slug/$', 'us_open_umbrella_board', {
    # combined to allow the resource to control open/close decision
    'rollout': _board_unauth_open_closed_react_config,
    'rollout_undecided': _board_unauth_open_closed_react_config,
    'control': _board_unauth_react_config,
    'control5': _board_unauth_react_config,
    'control5b': _board_unauth_react_config,
    'forced_open': _unauth_open_board_react_enabled_config,
    'forced_open5': _unauth_open_board_react_enabled_config,
    'forced_open5b': _unauth_open_board_react_enabled_config,
    'ao_react': _unauth_open_board_react_enabled_config,
    'ao_denzel': _board_denzel_config,
    'big_bundle_enabled': _board_unauth_open_closed_react_config,
    'big_bundle_control': _board_unauth_react_config,
    'closed_react': _board_unauth_react_config,
    'employees': _board_unauth_react_config},
    default_config_auth=_board_denzel_config,
    default_config_unauth=_board_unauth_react_config,
    exp_group_overwrite_unauth=True)

r(r'^/:username/:slug/edit/$', 'BoardPageWrapper',
    {
        'show_edit': True,
        'slug': '${slug}'
    },
    resource={
        'name': 'BoardResource',
        'options': {
            'username': '${username}',
            'slug': '${slug}',
            'field_set_key': 'detailed',
            'main_module_name': 'BoardPage'
        }
    },
    ios_deep_link='pinterest://board/${username}/${slug}',
    android_deep_link='pinterest://board/${username}/${slug}',
    canonical_url='/${username}/${slug}/',
    require_explicit_login=True,
    show_klp_bar=True,
    log={
        'view_type': ViewType.BOARD,
    },
    upwt_action_name=UpwtActionName.BOARD_PAGE_LOAD)

r(r'^/:username/:slug/invite/$', 'BoardPageWrapper',
    options={
        'board_collab_approval_request': True,
        'slug': '${slug}'
    },
    resource={
        'name': 'BoardResource',
        'options': {
            'username': '${username}',
            'slug': '${slug}',
            'field_set_key': 'detailed',
            'main_module_name': 'BoardPage'
        }
    },
    ios_deep_link='pinterest://board/${username}/${slug}',
    android_deep_link='pinterest://board/${username}/${slug}',
    canonical_url='/${username}/${slug}/',
    require_explicit_login=True,
    show_klp_bar=True,
    log={
        'view_type': ViewType.BOARD,
    },
    upwt_action_name=UpwtActionName.BOARD_PAGE_LOAD)

r(r'^/:username/:slug/pins/$', 'BoardPageWrapper',
    {
        'slug': '${slug}'
    },
    resource={
        'name': 'BoardResource',
        'options': {
            'username': '${username}',
            'slug': '${slug}',
            'field_set_key': 'detailed',
            'main_module_name': 'BoardPage'
        }
    },
    ios_deep_link='pinterest://board/${username}/${slug}',
    android_deep_link='pinterest://board/${username}/${slug}',
    canonical_url='/${username}/${slug}/',
    show_klp_bar=True,
    log={
        'view_type': ViewType.BOARD,
    },
    upwt_action_name=UpwtActionName.BOARD_PAGE_LOAD)


r(r'^/:username/:slug/followers/$', 'BoardPageWrapper',
    {
        'slug': '${slug}'
    },
    noindex=True,
    redirect='/${username}/${slug}/',
    log={
        'view_type': ViewType.BOARD,
        'view_parameter': ViewParameterType.BOARD_FOLLOWERS,
    },
    upwt_action_name=UpwtActionName.BOARD_PAGE_LOAD)

# shop space collection
r(r'^/shop_space/:section/:collection/$', 'ShopBoardPage',
    {},
    resource={
        'name': 'ShopSpaceCollectionResource',
        'options': {
            'section': '${section}',
            'collection': '${collection}'
        }
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_HOME
    },
    ios_deep_link='pinterest://shop_space/${section}/${collection}/',
    android_deep_link='pinterest://' + settings.CANONICAL_MAIN_DOMAIN + '/shop_space/${section}/${collection}/')

# shop board page
r(r'^/shop_pins/:section/:collection/$', 'ShopBoardPage',
    {},
    resource={
        'name': 'ShopSpaceCollectionResource',
        'options': {
            'section': '${section}',
            'collection': '${collection}'
        }
    },
    log={
        'view_type': ViewType.FEED,
        'view_parameter': ViewParameterType.FEED_BUYABLE_CATEGORY,
    })

_tried_it_feed_config = {
    'module': 'DidItFeedWrapper',
    'wrapper_name': 'DidItFeedWrapper',
    'content_only': True,
}

_tried_it_employee_feed_config = _tried_it_feed_config
_tried_it_employee_feed_config['content_only'] = False
_tried_it_employee_feed_config['options'] = {
    'employees_only': True,
}

rexp(r'^/_/_/tried_it_feed/', 'tried_it_feed', {
    'employees': _tried_it_feed_config,
    'control': {
        'module': 'Echo'
    }
})

rexp(r'^/_/_/tried_it_employee_feed/', 'tried_it_feed', {
    'employees': _tried_it_feed_config,
    'control': {
        'module': 'Echo'
    }
})

#
# Performance testing.  These are useful for profiling the performance of our framework.
#                   perf*  1  2  3  4
#              ------------------------
#              has header  _  x  x  x
#      has resource fetch  _  _  x  x
# has page metadata fetch  _  _  _  x
#
r(r'^/_/_/perf1/', 'Echo',
  {},
  content_only=True)
# empty content
r(r'^/_/_/perf2/', 'Echo',
  {})
# a resource fetch and no page metadata fetch
r(r'^/_/_/perf3/', 'Echo',
  {},
  resource={'name': 'CategoriesResource'})
# empty content, but has a resource fetch
r(r'^/_/_/perf4/', 'Echo',
  {},
  resource={'name': 'PinResource',
            'options': {'id': 13862711330220239}})

# React Grid Test Page
r(r'^/_/_/reactgrid/$', 'GridReactWrapper', {},
    resource={'name': 'UserHomefeedResource'},
    require_authentication=True, require_explicit_login=True)

# React base page
r(r'^/_/_/reactperf1/',
    pure_react=True)

r(r'^/one_tap_login/$', 'MobileWebLoginRedirectWrapper',
    {'browser': '?{browser}',
     'expiration': '?{expiration}',
     'group': '?{group}',
     'name': '?{name}',
     'token': '?{token}',
     'url': '?{url}',
     'user_id': '?{user_id}'},
    {},
    content_only=True,
    force_ssnunjucks=True,
    hide_interstitial=True)

r(r'^/_/_/experiments/config/$', 'InternalExperimentsConfig',
    resource={'name': 'ExperimentsConfigResource'})
