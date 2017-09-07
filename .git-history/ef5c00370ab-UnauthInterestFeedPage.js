/* eslint react/jsx-no-bind:0 */
/* eslint react/forbid-prop-types:0 */
/* eslint react/no-did-mount-set-state:0 */
// @flow

import React, { Component, PropTypes } from 'react';
import AmpWrapper from 'app/common/react/components/growth/unauth/AmpWrapper/AmpWrapper';
import AppBanner from 'app/common/react/components/growth/unauth/AppBanner/AppBanner';
import AppInterstitial from 'app/common/react/components/growth/unauth/header/AppInterstitial/AppInterstitial';
import Breadcrumbs from 'app/common/react/components/growth/unauth/Breadcrumbs/Breadcrumbs';
import DebugInfo from 'app/common/react/components/common/DebugInfo/DebugInfo';
import DefaultCSS from 'app/common/react/components/growth/unauth/DefaultCSS';
import ErrorModal from 'app/common/react/components/growth/unauth/ErrorModal/ErrorModal';
import EuCookieBar from 'app/common/react/components/growth/unauth/header/EuCookieBar/EuCookieBar';
import ExpandableKlpDescription from 'app/common/react/components/growth/unauth/ExpandableKlpDescription/ExpandableKlpDescription';
import FacebookConnectButton from 'app/common/react/components/growth/unauth/signup/FacebookConnectButton/FacebookConnectButton';
import FullPageModal from 'app/common/react/components/growth/unauth/FullPageModal/FullPageModal';
import FullPageModalCSS from 'app/common/react/components/growth/unauth/FullPageModal/FullPageModalCSS';
import GiftWrap from 'app/common/react/components/growth/unauth/GiftWrap/GiftWrap';
import GiftWrapCSS from 'app/common/react/components/growth/unauth/GiftWrap/GiftWrapCSS';
import GiftWrapUtils from 'app/common/lib/GiftWrapUtils';
import GoogleConnectButton from 'app/common/react/components/growth/unauth/signup/GoogleConnectButton/GoogleConnectButton';
import HeaderCSS from 'app/common/react/components/growth/unauth/header/HeaderCSS';
import LeafSnippetKLP from 'app/common/react/components/growth/unauth/pin/RichSnippet/LeafSnippetKLP';
import logo from 'app/common/react/components/growth/unauth/lib/images/logo';
import PageContext from 'app/common/react/components/growth/unauth/PageContext';
import PinAttributionTitleCSS from 'app/common/react/components/growth/unauth/pin/PinAttributionTitle/PinAttributionTitleCSS';
import PinCSS from 'app/common/react/components/growth/unauth/pin/PinCSS';
import PinDescriptionCSS from 'app/common/react/components/growth/unauth/pin/PinDescription/PinDescriptionCSS';
import PinGrid from 'app/common/react/components/growth/unauth/PinGrid/PinGrid';
import PinGridAltCSS from 'app/common/react/components/growth/unauth/PinGrid/PinGridAltCSS';
import PinGridCSS from 'app/common/react/components/growth/unauth/PinGrid/PinGridCSS';
import PinSnippetList from 'app/common/react/components/growth/unauth/pin/RichSnippet/PinSnippetList';
import RelatedInterestsSection from 'app/common/react/components/growth/unauth/RelatedInterestsSection/RelatedInterestsSection';
import RelatedInterestsSectionCSS from 'app/common/react/components/growth/unauth/RelatedInterestsSection/RelatedInterestsSectionCSS';
import ResetCSS from 'app/common/react/components/growth/unauth/ResetCSS';
import ResourceFactory from 'app/common/lib/ResourceFactory';
import SeamlessExperiment from 'app/common/lib/SeamlessExperiment';
import SignupCSS from 'app/common/react/components/growth/unauth/signup/SignupCSS';
import SignupModalUtils from 'app/common/react/components/growth/unauth/lib/SignupModalUtils';
import trackRegisterAction from 'app/common/lib/util/trackRegisterAction';
import type ExperimentsClient from 'app/common/lib/ExperimentsClient';
import UnauthBanner from 'app/common/react/components/growth/unauth/UnauthBanner/UnauthBanner';
import UnauthBannerCSS from 'app/common/react/components/growth/unauth/UnauthBanner/UnauthBannerCSS';
import UnauthHeader from 'app/common/react/components/growth/unauth/header/UnauthHeader/UnauthHeader';
import UnauthUsage from 'app/common/lib/UnauthUsage';
import { base64EncodingPrefix } from 'app/common/react/components/growth/unauth/lib/ImageUtils.js';
import { getGridItemWidth } from 'app/common/lib/react/gridUtils';
import { type I18nType } from 'app/common/lib/i18n';
import { type PinType } from 'app/common/react/components/growth/unauth/lib/PropTypes';
import FullPageSignup, { SignupSource, SignupTypes } from 'app/common/react/components/growth/unauth/signup/FullPageSignup/FullPageSignup';
import withI18n, { I18nPropType } from 'app/common/lib/react/withI18n';
import withUnauthSeoExperiments, { ExperimentsPropType } from 'app/common/lib/react/withUnauthSeoExperiments';

type ContextWithUserAgent = {
  userAgent: {
    canUseNativeApp: boolean,
    isMobile: boolean,
    isTablet: boolean,
  },
};
type ContextWithIsAuthenticated = { isAuthenticated: boolean };
type ContextWithIsBot = { isBot: boolean };
type ContextWithIsMobile = { isMobile: boolean };
type ContextWithIsTablet = { isTablet: boolean };
type ContextWithLocale = { locale: string };
type ContextWithPageType = { pageType: string };
type ContextWithSearchReferrer = { searchReferrer: string };

type Context = ContextWithPageType
  & ContextWithUserAgent
  & ContextWithLocale
  & ContextWithIsMobile
  & ContextWithIsAuthenticated
  & ContextWithIsTablet
  & ContextWithSearchReferrer
  & ContextWithIsBot;

type BookmarksType = Array<string>;
type BreadcrumbsType = {
  breadcrumb_url: string,
  display_name: string,
  full_local_url: string,
};

type InterestType = {
  id: string,
  no_gift_wrap: boolean,
  url_name: string,
  id: string,
  name: string,
  description: string,
  breadcrumbs: Array<BreadcrumbsType>,
};

type Props = {
  data: {
    bookmarks: BookmarksType,
    related_interests: Array<InterestType>,
    interest_feed: Array<{
      id: string,
      base64?: string,
      type: string,
    }>,
    search_debug_data: any,
    page_size: number,
  },
  i18n: I18nType,
  options: {
    interest_data: InterestType,
    interest_options: {},
  },
  seoUnauthExperiments: ExperimentsClient,
};

type State = {
  email: string,
  emailValidationError: string,
  passwordValidationError: string,
  showSignupModal: boolean,
  showGiftwrap: boolean,
  modalType: $Keys<SignupTypes>,
  openPinInCurrentTab: boolean,
  signupSource: ?string,
};

const styles = {
  whiteBackground: {
    backgroundColor: '#fff',
    position: 'fixed',
    top: '0',
    left: '0',
    right: '0',
    bottom: '0',
    zIndex: '-1',
  },
  appContent: {
    padding: 0,
  },
  wrapper: {
  },
  interestHeaderWrapper: {
    backgroundColor: '#fff',
    marginBottom: '16px',
    paddingBottom: '22px',
  },
  centerWrapper: {
    position: 'relative',
  },
  description: {
    color: '#555',
    fontSize: '14px',
    margin: '11px 0 0 10px',
    maxWidth: '618px',
  },
  klpTitle: {
    color: '#555',
    fontSize: '48px',
    fontWeight: 'bold',
    paddingTop: '20px',
    marginLeft: '5px',
  },
  mwebKlpTitle: {
    fontSize: '40px',
    fontWeight: 'bold',
    margin: '15px 10px',
    textAlign: 'center',
  },
  mwebContentWrapper: {
    position: 'absolute',
    left: '0px',
    top: '100%',
    right: '0px',
    padding: '0px',
  },
  mwebRelatedInterests: {
    marginBottom: '16px',
  },
  noScroll: {
    position: 'fixed',
    top: 0,
    bottom: 0,
    right: 0,
    left: 0,
  },
  hidden: {
    display: 'none',
  },
  mwebTitle: {
    fontSize: '36px',
    fontWeight: 'bold',
    color: '#555',
    marginTop: '18px',
    marginBottom: '18px',
  },
  mwebHeaderWrapper: {
    backgroundColor: '#fff',
    paddingBottom: '14px',
    marginBottom: '18px',
  },
  mwebPinterestHeader: {
    height: '64px',
    borderBottom: '1px solid #efefef',
  },
  mwebHeaderLogo: {
    display: 'inline-block',
    verticalAlign: 'middle',
    margin: '12px 16px 12px 0',
  },
  mwebPinterestHeaderText: {
    display: 'inline-block',
    verticalAlign: 'middle',
    fontWeight: 'bold',
    fontSize: '18px',
    color: '#555',
  },
};

const cssStyles = (
  context: ContextWithIsMobile
    & ContextWithPageType
    & ContextWithUserAgent
    & ContextWithIsTablet
    & ContextWithIsAuthenticated
    & ContextWithLocale,
  pins: Array<PinType>,
  seoUnauthExperiments: ExperimentsClient,
  numServerRenderedPins: number,
) => {
  const pinGridCss = !numServerRenderedPins || numServerRenderedPins === 0 ? PinGridCSS(context.userAgent.isMobile) :
    PinGridAltCSS(pins, context, seoUnauthExperiments, false, numServerRenderedPins);
  return (
    ResetCSS() +
    DefaultCSS() +
    FullPageModalCSS() +
    PinCSS() +
    SignupCSS(context.userAgent.isMobile) +
    pinGridCss +
    PinDescriptionCSS(seoUnauthExperiments) +
    PinAttributionTitleCSS(context.locale, seoUnauthExperiments) +
    RelatedInterestsSectionCSS() +
    UnauthBannerCSS() +
    GiftWrapCSS() +
    HeaderCSS(context.userAgent.isMobile, context.userAgent.isTablet)
  );
};

const renderBreadcrumbs = (breadcrumbs: ?Array<BreadcrumbsType>) => {
  if (breadcrumbs) {
    return (<Breadcrumbs breadcrumbs={breadcrumbs} />);
  }
  return undefined;
};

const renderExpandableDescription = (description: ?string) => {
  if (description) {
    return (<ExpandableKlpDescription description={description} />);
  }
  return undefined;
};

function readAttrs(selector: string, attr: string) {
  if (document && 'querySelectorAll' in document) {
    return Array.from(document.querySelectorAll(selector)).reduce((map, node) => {
      const uuid = node.getAttribute('data-uuid');
      if (uuid) {
        map[uuid] = node.getAttribute(attr);
      }
      return map;
    }, {});
  } else {
    return {};
  }
}

export class UnauthInterestFeedPage extends Component<void, Props, State> {
  constructor(props: Props) {
    super(props);

    this.state.showGiftwrap = !this.props.options.interest_data.no_gift_wrap;

    // On client, parse base64 strings from dom and add them back to the correct pin prop
    if (!__SERVER__) {
      window.base64SrcCache = readAttrs('img[src^="data:image/"]', 'src');
      window.base64SrcSetCache = readAttrs('img[srcset*="data:image/"]', 'srcset');
      for (const key in window.base64SrcSetCache) {
        const srcSetString = window.base64SrcSetCache[key];
        const base64String = srcSetString.split(' 1x, ')[0];
        const base64StringNoPrefix = base64String.replace(base64EncodingPrefix, '');
        props.data.interest_feed.forEach((item) => {
          if (item.id === key) {
            item.base64 = base64StringNoPrefix;
          }
        });
      }
      for (const key in window.base64SrcCache) {
        const base64String = window.base64SrcCache[key];
        const base64StringNoPrefix = base64String.replace(base64EncodingPrefix, '');
        props.data.interest_feed.forEach((item) => {
          if (item.id === key) {
            item.base64 = base64StringNoPrefix;
          }
        });
      }
    }
  }

  state: State = {
    email: '',
    emailValidationError: '',
    passwordValidationError: '',
    showSignupModal: false,
    showGiftwrap: false,
    modalType: SignupTypes.signup,
    openPinInCurrentTab: false,
    signupSource: null,
  };

  componentDidMount() {
    const fromNavigate = GiftWrapUtils.from_navigate_precise();
    if (fromNavigate &&
      document.referrer.indexOf('/explore/' + this.props.options.interest_data.url_name + '/') < 0 &&
      GiftWrapUtils.is_gift_wrap_enabled() && SeamlessExperiment.shouldShowSignupModal() &&
      !SignupModalUtils.checkIfSignupModalDisabled()) {
      this.setState({ showSignupModal: true });
      trackRegisterAction('unauth_navigate.UnauthInterestFeedPage');
    }
    UnauthUsage.logUrl();
    UnauthUsage.logUnauthImageFeed(this.props.data.interest_feed.filter(item => item.type === 'pin'));
  }

  context: Context;

  handleLoginError = (error: { formattedError: string, message: string, type: string }, email: string) => {
    if (!error) {
      this.showSignupModal(SignupTypes.login, SignupSource.login); // Default to login
    }

    this.setState({ email });

    if (error.type === 'email') { // failed input validation
      this.setState({ emailValidationError: error.message });
      this.showSignupModal(SignupTypes.login, SignupSource.login);
    } else if (error.type === 'password') { // failed input validation
      this.setState({ passwordValidationError: error.message });
      this.showSignupModal(SignupTypes.login, SignupSource.login);
    } else if (error.type === 'login') { // failed login request
      if (error.formattedError === 'invalidEmail') {
        this.setState({ emailValidationError: error.message });
        this.showSignupModal(SignupTypes.signup, SignupSource.defaultSource);
      } else {
        this.setState({ passwordValidationError: error.message });
        this.showSignupModal(SignupTypes.login, SignupSource.login);
      }
    }
  }

  showSignupModal(
    type: $Keys<SignupTypes>,
    signupSource: string,
    e?: SyntheticEvent,
  ) {
    this.setState({ showSignupModal: true, modalType: type, signupSource });
    trackRegisterAction('plain_signup_modal_view');
    if (e) {
      e.preventDefault();
    }
  }

  pinImageClickHandler = (event: SyntheticEvent, pin: PinType) => {
    event.preventDefault();
    window.location = '/pin/' + pin.id + '/';
  };

  loadPins(
    interest: string,
    interestName: string,
    pageSize: number,
    pins: Array<PinType>,
    bookmarks: BookmarksType,
    callback: (data: any, bookmarks: BookmarksType) => void,
  ) {
    const feedResource = ResourceFactory.create('InterestsFeedResource', {
      interest,
      add_vase: true,
      interest_name: interestName,
      page_size: pageSize,
      pins_only: true,
      bookmarks,
      field_set_key: 'unauth_react',
    });
    feedResource.callGet()
      .then((response) => {
        callback(
          response.resource_response.data,
          response.bookmarks);
      });
  }

  mobilePage(
    pins: Array<PinType>,
    pinImageWidthMin: number,
    pinImageWidthMax: number,
    base64Group: ?string,
  ) {
    const { seoUnauthExperiments } = this.props;
    if (['enabled'].includes(seoUnauthExperiments.v2ActivateExperiment('amp_wrapper_klp'))) {
      return <AmpWrapper />;
    }

    const { data: { related_interests }, options: { interest_data: interest } } = this.props;
    const canUseNativeApp = this.context.userAgent.canUseNativeApp;
    let interstitial = null;
    let mwebContentWrapperStyle = {};
    const pinImageSize = '170x';
    const srcSet = {
      oneXSizes: ['170x', '236x'], twoXSizes: ['236x'], threeXSizes: ['474x', '236x'],
    };
    const interstitialReplacement = this.context.searchReferrer === 'google' || this.context.isBot;
    if (canUseNativeApp && !this.state.showSignupModal) {
      if (interstitialReplacement) {
        interstitial = (<AppBanner pins={pins} />);
      } else {
        interstitial = (
          <AppInterstitial
            pinImageSize={pinImageSize}
            pins={pins}
            srcSet={srcSet}
            title={interest.name}
          />
          );
        mwebContentWrapperStyle = styles.mwebContentWrapper;
      }
    }

    return (
      <div style={this.state.showSignupModal ? styles.noScroll : null} >
        <div style={styles.whiteBackground} />
        {interstitial}
        <div className="mwebContentWrapper" style={mwebContentWrapperStyle}>
          {interstitialReplacement ?
            <div style={styles.mwebHeaderWrapper}>
              <div style={styles.mwebPinterestHeader}>
                <div className="gridCentered">
                  <div style={styles.mwebHeaderLogo}>{logo(40, false)}</div>
                  <div style={styles.mwebPinterestHeaderText}>{this.props.i18n._('Pinterest')}</div>
                </div>
              </div>
              <div className="gridCentered" style={styles.mwebTitle}>
                {interest.name}
              </div>
              <div className="gridCentered">
                <RelatedInterestsSection relatedInterests={related_interests} titleStyle={'mwebBrioHeader'} />
              </div>
            </div> :
            <div>
              <h1 style={styles.mwebKlpTitle}> {interest.name} </h1>
              <div className="gridCentered" style={styles.mwebRelatedInterests}>
                {renderExpandableDescription(interest.description)}
                <RelatedInterestsSection
                  pinImageWidthMax={pinImageWidthMax}
                  pinImageWidthMin={pinImageWidthMin}
                  relatedInterests={related_interests}
                />
              </div>
            </div>}
          {this.renderMobileContent(pins, pinImageWidthMin, pinImageWidthMax, pinImageSize, srcSet, base64Group)}
        </div>
      </div>
    );
  }

  desktopPage(
    pins: Array<PinType>,
    pinImageWidthMin: number,
    pinImageWidthMax: number,
    numServerRenderedPins: number,
    base64Group: ?string,
  ) {
    const { data: { bookmarks, related_interests, search_debug_data, page_size },
      options: { interest_data: interest } } = this.props;
    let header = null;
    let appBanner = false;
    const breadcrumbs = interest ? interest.breadcrumbs : null;
    const pinImageSize = '736x';
    const srcSet = {
      oneXSizes: ['236x'], twoXSizes: ['236x'], threeXSizes: ['474x', '236x'],
    };
    if (this.context.userAgent.isTablet) {
      header = (
        <UnauthHeader
          handleLoginError={this.handleLoginError}
          numServerRenderedPins={numServerRenderedPins}
          onLoginClick={this.showSignupModal.bind(this, SignupTypes.login, SignupSource.login)}
          onSignupClick={this.showSignupModal.bind(this, SignupTypes.signup, SignupSource.defaultSource)}
        />
      );
      appBanner = true;
    } else {
      header = (
        <UnauthHeader
          handleLoginError={this.handleLoginError}
          numServerRenderedPins={numServerRenderedPins}
          onLoginClick={this.showSignupModal.bind(this, SignupTypes.login, SignupSource.login)}
          onSignupClick={this.showSignupModal.bind(this, SignupTypes.signup, SignupSource.defaultSource)}
        />
      );
    }
    const seoUnauthExperiments = this.props.seoUnauthExperiments;

    let banner = null;
    if (appBanner) {
      banner = <AppBanner pins={pins} />;
    } else if (!this.state.showSignupModal && this.state.showGiftwrap) {
      if (seoUnauthExperiments.v2ActivateExperiment('unauth_banner_klp_3') === 'enabled') {
        banner = (
          <UnauthBanner
            onLoginClick={this.showSignupModal.bind(this, SignupTypes.login, SignupSource.login)}
            pins={pins && pins.constructor === Array ? pins.slice(0, 4) : []}
          />);
      } else {
        banner = (
          <GiftWrap
            onLoginClick={this.showSignupModal.bind(this, SignupTypes.login, SignupSource.login)}
            pageType={'klp'}
          />);
      }
    }

    return (
      <div style={this.state.showSignupModal ? styles.noScroll : null} >
        <div style={styles.whiteBackground} />
        <EuCookieBar />
        {header}
        <div data-test-interestContent style={styles.appContent}>
          <div style={styles.interestHeaderWrapper}>
            {renderBreadcrumbs(breadcrumbs)}
            <div className="gridCentered" style={styles.centerWrapper}>
              <h1 style={styles.klpTitle}> {interest.name} </h1>
              {interest.description ? <div style={styles.description}>{interest.description}</div> : null}
              <RelatedInterestsSection
                newTabOnClick
                pinImageWidthMax={pinImageWidthMax}
                pinImageWidthMin={pinImageWidthMin}
                relatedInterests={related_interests}
              />
            </div>
          </div>
          {search_debug_data && Object.keys(search_debug_data).length !== 0
            ? <DebugInfo data={search_debug_data} />
            : null}
          <PinGrid
            base64Group={base64Group}
            bookmarks={[bookmarks]}
            desktopUnauthRankingLoggingData={this.props.options.interest_data}
            items={pins}
            loadPins={this.loadPins.bind(this,
                           interest.id,
                           interest.name,
                           page_size)}
            pinImageClickHandler={this.state.openPinInCurrentTab ? this.pinImageClickHandler : null}
            pinImageSize={pinImageSize}
            pinImageWidthMax={pinImageWidthMax}
            pinImageWidthMin={pinImageWidthMin}
            showSignupModal={this.showSignupModal.bind(this, SignupTypes.signup, SignupSource.saveButton)}
            srcSet={srcSet}
            numServerRenderedPins={numServerRenderedPins}
          />
          {banner}
        </div>
      </div>
    );
  }

  renderMobileContent(
    pins: Array<PinType>,
    pinImageWidthMin: number,
    pinImageWidthMax: number,
    pinImageSize: string,
    srcSet: Object,
    base64Group: ?string) {
    const { data: { bookmarks, page_size },
      options: { interest_data: interest } } = this.props;
    const showSignupModal = this.showSignupModal.bind(this, SignupTypes.signup, SignupSource.defaultSource);

    return (
      <div>
        <PinGrid
          base64Group={base64Group}
          bookmarks={[bookmarks]}
          items={pins}
          loadPins={this.loadPins.bind(this,
            interest.id,
            interest.name,
            page_size)}
          pinImageSize={pinImageSize}
          pinImageWidthMax={pinImageWidthMax}
          pinImageWidthMin={pinImageWidthMin}
          showSignupModal={showSignupModal}
          srcSet={srcSet}
        />
      </div>
    );
  }

  renderFullPageSignup = () => {
    const { email, emailValidationError, passwordValidationError } = this.state;
    return (
      <FullPageSignup
        email={email}
        emailValidationError={emailValidationError}
        passwordValidationError={passwordValidationError}
        container="UnauthInterestFeedPage"
        signupSource={this.state.signupSource}
        type={this.state.modalType}
      />
    );
  }

  render() {
    const base64Group = this.props.seoUnauthExperiments.v2ActivateExperiment('base64_pin_images_klp');
    const isMobile = this.context.userAgent.isMobile;
    const pins = this.props.data.interest_feed.filter(item => item.type === 'pin');
    const pinImageWidthStandard = getGridItemWidth(isMobile);
    const pinImageWidthMax = pinImageWidthStandard;
    const pinImageWidthMin = pinImageWidthStandard;
    const seoUnauthExperiments = this.props.seoUnauthExperiments;
    /* eslint react/no-danger:0 */
    const numServerRenderedPins = this.context.isBot || isMobile ? 0 : 16;
    const cssStylesString = cssStyles(this.context, pins, seoUnauthExperiments, numServerRenderedPins);
    return (
      <PageContext page="klp" viewData={{ interest: this.props.options.interest_data.url_name }}>
        <div style={styles.wrapper}>
          <style dangerouslySetInnerHTML={{ __html: cssStylesString }} />
          {isMobile ? this.mobilePage(pins, pinImageWidthMin, pinImageWidthMax, base64Group) :
            this.desktopPage(pins, pinImageWidthMin, pinImageWidthMax, numServerRenderedPins, base64Group)}
          <PinSnippetList pins={pins} />
          <LeafSnippetKLP interest={this.props.options.interest_data} pins={pins} mainEntityOfPage={false} />
          {this.state.showSignupModal ? <FullPageModal renderContent={this.renderFullPageSignup} /> : null}
          <ErrorModal />
          <div style={styles.hidden}>
            <FacebookConnectButton buttonText={this.props.i18n._('Log in with Facebook')} />
            <GoogleConnectButton />
          </div>
        </div>
      </PageContext>
    );
  }
}

UnauthInterestFeedPage.propTypes = {
  data: PropTypes.object.isRequired,
  i18n: I18nPropType.isRequired,
  options: PropTypes.shape({
    interest_data: PropTypes.object.isRequired,
    interest_options: PropTypes.object.isRequired,
  }),
  seoUnauthExperiments: ExperimentsPropType,
};

UnauthInterestFeedPage.contextTypes = {
  browserName: PropTypes.string,
  country: PropTypes.string,
  isAuthenticated: PropTypes.bool.isRequired,
  isBot: PropTypes.bool,
  locale: PropTypes.string.isRequired,
  searchReferrer: PropTypes.string.isRequired,
  userAgent: PropTypes.shape({
    canUseNativeApp: PropTypes.bool.isRequired,
    isMobile: PropTypes.bool.isRequired,
    isTablet: PropTypes.bool.isRequired,
  }).isRequired,
};

export default withUnauthSeoExperiments(withI18n(UnauthInterestFeedPage));
