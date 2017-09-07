/* eslint react/jsx-no-bind:0 */

import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import contextLog from 'app/common/redux/actions/contextLog';
import DeepLink from 'app/common/react/components/growth/unauth/lib/Deeplink';
import DeeplinkRoutes from 'app/common/react/components/growth/unauth/lib/DeeplinkRoutes';
import SignupModalUtils from 'app/common/react/components/growth/unauth/lib/SignupModalUtils';
import trackRegisterAction from 'app/common/lib/util/trackRegisterAction';
import urlUtil from 'app/common/lib/urlUtil';
import withI18n, { I18nPropType } from 'app/common/lib/react/withI18n';
import withUnauthSeoExperiments, { ExperimentsPropType } from 'app/common/lib/react/withUnauthSeoExperiments';

const styles = {
  list: {
    height: '40px',
    overflow: 'hidden',
  },
  wrapper: {
    display: 'inline-block',
    height: '36px',
    borderRadius: '4px',
    margin: '0 2px 40px',
    position: 'relative',
  },
  labelText: {
    color: '#fff',
    fontSize: '14px',
    fontWeight: 'bold',
    padding: '10px 14px',
    textAlign: 'center',
    WebkitFontSmoothing: 'antialiased',
  },
  mwebRelatedInterestsTitle: {
    color: '#9a9a9a',
    fontSize: '13px',
    textTransform: 'uppercase',
    opacity: '0.6',
    textAlign: 'center',
    fontWeight: 'bold',
    marginBottom: '20px',
  },
  overlay: {
    backgroundColor: 'black',
    height: '100%',
    width: '100%',
    position: 'absolute',
    top: '0',
    left: '0',
    borderRadius: '4px',
  },
  mwebBrioHeader: {
    fontSize: '14px',
    fontWeight: 'bold',
    marginBottom: '5px',
    color: '#555',
    marginLeft: '2px',
  },
};

class RelatedInterestsSection extends Component {

  componentDidMount() {
    trackRegisterAction('unauth.related_interests.loaded');
  }

  handleClick = (interestName, interestUrlId, interestId, position, e) => {
    const { pageType, currentUrl } = this.context;

    trackRegisterAction('unauth.related_interest.clicked');
    this.props.dispatch(contextLog(PCONST.thrift.EventType.CLICK, {
      view: this.context.logging.viewType,
      viewParameter: this.context.logging.viewParameter,
      element: PCONST.thrift.ElementType.FLOWED_INTEREST,
      component: PCONST.thrift.ComponentType.INTEREST_GRID,
      unauth_related_interest_id: interestId,
      unauth_related_interest_position: position,
      unauth_page_type: pageType,
      unauth_page_id: urlUtil.getUnauthPageId(pageType, currentUrl),
    }));
    if (this.props.noModalOnNavigate) {
      SignupModalUtils.disableSignupModalForNextPage();
      trackRegisterAction('category_jump_banner_click_' + interestName);
    }

    const deepLink = new DeepLink(this.props.seoUnauthExperiments,
      this.context.userAgent.raw,
      this.context.userAgent.platform,
      this.context.userAgent.platformVersion);
    if (deepLink.shouldDeepLink(document.referrer,
        this.context.userAgent,
        this.context.isAuthenticated,
        this.context.isAndroidLite)) {
      e.preventDefault();
      deepLink.navigateToDeepLink(this.context.unauthId,
        DeeplinkRoutes.buildExploreDeeplinks(interestUrlId));
    }
  }

  render() {
    const isMobile = this.context.userAgent.isMobile;

    if (this.props.relatedInterests.length === 0) {
      return (null);
    }

    const backgroundColors = ['#9FA994', '#DBB6AB', '#D3BE9C', '#8EA8AF', '#C0B19A', '#C99E92', '#B6C3A7', '#A8A4AE',
      '#C0B68D', '#9BA8AC', '#BF9D94'];

    let titleStyle = styles.mwebRelatedInterestsTitle;

    // using negative margin to isolate modifications since this is experiment and we may not ship.
    // If we ship, will implement in a different way.
    let listStyle = isMobile ? { ...styles.list, textAlign: 'center' } :
      { ...styles.list, padding: '0 5px' };

    if (this.props.titleStyle === 'mwebBrioHeader') {
      listStyle = styles.list;
      titleStyle = styles.mwebBrioHeader;
    }

    const relatedInterestsSectionStyle = this.props.style || (isMobile ? { marginTop: '6px' } : { marginTop: '20px' });

    return (
      <div data-test-relatedInterests style={relatedInterestsSectionStyle}>
        {isMobile ? <div style={titleStyle}>{this.props.i18n._('Related Topics')}</div> : null}
        <ul style={listStyle}>
          {this.props.relatedInterests.map((interest, idx) => {
            const colorIndex = idx % backgroundColors.length;
            const backgroundColor = backgroundColors[colorIndex];
            const wrapperStyle = { ...styles.wrapper, backgroundColor };
            return (
              <li
                className="RelatedInterestsSection__listItem"
                key={idx}
                style={wrapperStyle}>
                <a
                  href={interest.canonical_url}
                  onClick={this.handleClick.bind(this,
                    interest.name, interest.url_name, interest.id, idx)}
                  target={this.props.newTabOnClick ? '_blank' : null}>
                  <h2 style={styles.labelText}>
                    {interest.name}
                  </h2>
                </a>
              </li>
            );
          })}
        </ul>
      </div>
    );
  }
}

RelatedInterestsSection.propTypes = {
  dispatch: PropTypes.func.isRequired,
  i18n: I18nPropType.isRequired,
  newTabOnClick: PropTypes.bool,
  noModalOnNavigate: PropTypes.bool,
  relatedInterests: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string,
    url: PropTypes.string,
    image: PropTypes.string,
  })),
  seoUnauthExperiments: ExperimentsPropType,
  style: PropTypes.shape({
    marginTop: PropTypes.string,
  }),
  titleStyle: PropTypes.string,
};

RelatedInterestsSection.contextTypes = {
  country: PropTypes.string,
  currentUrl: PropTypes.string,
  isAndroidLite: PropTypes.bool.isRequired,
  isAuthenticated: PropTypes.bool.isRequired,
  isBot: PropTypes.bool.isRequired,
  locale: PropTypes.string.isRequired,
  logging: PropTypes.shape({
    viewParameter: PropTypes.number,
    viewType: PropTypes.number.isRequired,
  }),
  pageType: PropTypes.string,
  userAgent: PropTypes.shape({
    canUseNativeApp: PropTypes.bool.isRequired,
    isMobile: PropTypes.bool.isRequired,
    isTablet: PropTypes.bool.isRequired,
    platform: PropTypes.string.isRequired,
    platformVersion: PropTypes.arrayOf(PropTypes.number),
    raw: PropTypes.string.isRequired,
  }).isRequired,
};

RelatedInterestsSection.defaultProps = {
  newTabOnClick: false,
  noModalOnNavigate: false,
};

export default connect()(withUnauthSeoExperiments(withI18n(RelatedInterestsSection)));
