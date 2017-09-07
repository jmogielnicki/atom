/* eslint react/no-unused-prop-types:0 */

import React, { Component, PropTypes } from 'react';
import * as StringUtil from 'app/common/lib/StringUtil';
import Button from 'app/common/react/components/growth/unauth/Button/Button';
import cx from 'classnames';
import LoginUpsellPopup from 'app/common/react/components/growth/unauth/open/education/LoginUpsell/LoginUpsellPopup';
import logo from 'app/common/react/components/growth/unauth/lib/images/logo';
import storage from 'app/common/lib/Storage';
import trackRegisterAction from 'app/common/lib/util/trackRegisterAction';
import withI18n, { I18nPropType } from 'app/common/lib/react/withI18n';
import { Avatar, Touchable } from 'gestalt';

const styles = {
  caret: {
    background: '#fff',
    transform: 'rotate(45deg)',
    position: 'absolute',
    top: '63.5px',
  },
  caretShadow: {
    boxShadow: '0px 1px 10px 0px rgba(153, 153, 153, 0.5)',
  },
  discoverText: {
    color: '#434343',
    fontSize: '18px',
    fontWeight: 'bold',
    marginLeft: '14px',
    WebkitFontSmoothing: 'antialiased',
    MozOsxFontSmoothing: 'grayscale',
  },
  leftHeaderContent: {
    display: 'flex',
    flex: '1',
    alignItems: 'center',
  },
  header: {
    top: '0',
    backgroundColor: '#fff',
    borderBottom: '1px solid #ccc',
    width: '100%',
    minWidth: '770px',
  },
  headerContainer: {
    height: '64px',
    display: 'flex',
    alignItems: 'center',
    margin: '0 32px',
  },
  alignedHeaderContainer: {
    height: '64px',
    display: 'flex',
    alignItems: 'center',
    margin: '0 16px',
  },
  rightHeaderContent: {
    order: 1,
    WebkitOrder: 1,
    msFlexOrder: 1,
  },
  barButtonsWrapper: {
    display: 'inline-flex',
  },
  leftButton: {
    marginRight: '8px',
  },
  loginButton: {
    display: 'inline-block',
    marginTop: '0px',
    fontSize: '14px',
    padding: '0px',
    width: '128px',
    height: '40px',
    borderRadius: '4px',
    verticalAlign: 'middle',
  },
  loginUpsellPopup: {
    position: 'absolute',
    right: '0px',
    top: '74px',
  },
  logoContainer: {
    cursor: 'pointer',
    display: 'block',
    float: 'left',
    height: '28px',
    width: '28px',
    verticalAlign: 'middle',
  },
  rightContentContainer: {
    position: 'relative',
  },
  signupButton: {
    display: 'inline-block',
    lineHeight: '36px',
    marginTop: '0px',
    padding: '0px',
    fontSize: '14px',
    width: '128px',
    height: '40px',
    borderRadius: '4px',
  },
  circleLogo: {
    display: 'inline-block',
    verticalAlign: 'middle',
  },
  forgotAccountLink: {
    fontSize: '12px',
    fontWeight: 'bold',
    marginTop: '8px',
  },
  profilePic: {
    cursor: 'pointer',
    display: 'inline-block',
    width: '40px',
    verticalAlign: 'middle',
  },
  profilePicButtons: {
    display: 'inline-block',
    height: '40px',
    padding: '10px 0 0 24px',
    verticalAlign: 'middle',
  },
  continueLink: {
    color: '#555',
    cursor: 'pointer',
    display: 'block',
    fontSize: '14px',
    fontWeight: 'bold',
    lineHeight: '16px',
  },
  notYouLink: {
    color: '#555',
    cursor: 'pointer',
    display: 'block',
    fontSize: '12px',
    fontWeight: 'bold',
    lineHeight: '14px',
    paddingTop: '2px',
  },
};

const LOCALSTORAGE_UNAUTH_PUBLIC_PROFILE = 'unauthPublicProfileStorage';

class UnauthHeader extends Component {
  constructor(props) {
    super(props);
    this.state = {
      headerStyle: null,
      userInfo: null,
    };
  }

  componentDidMount() {
    this.setHeaderStyle();
  }

  setHeaderStyle() {
    const userInfo = storage.localStorage.getItem(LOCALSTORAGE_UNAUTH_PUBLIC_PROFILE);
    if (userInfo) {
      this.setState({ headerStyle: 'personalized', userInfo });
    } else {
      this.setState({ headerStyle: 'default' });
    }
  }

  handleNotYouClick() {
    this.setState({ headerStyle: 'default' });
    storage.localStorage.removeItem(LOCALSTORAGE_UNAUTH_PUBLIC_PROFILE);
  }

  renderSignupButton(colorClass, additionalStyles) {
    const classNames = cx(colorClass, 'headerSignupButton');
    return (
      <Button
        className={classNames}
        numServerRenderedPins={this.props.numServerRenderedPins}
        onClick={(e) => { trackRegisterAction('unauth.signup_button.click'); this.props.onSignupClick(e); }}
        key="signup"
        styleOverrides={{ ...styles.signupButton, ...additionalStyles }}>
        {this.props.i18n._('Sign up')}
      </Button>
    );
  }

  renderLoginButton(colorClass, additionalStyles) {
    const classNames = cx(colorClass, 'headerLoginButton');

    const loginButton = (
      <div
        key="loginButton"
        ref={(c) => { this._loginButton = c; }}>
        <Button
          className={classNames}
          numServerRenderedPins={this.props.numServerRenderedPins}
          onClick={(e) => { trackRegisterAction('unauth.login_button.click'); this.props.onLoginClick(e); }}
          styleOverrides={{ ...styles.loginButton, ...additionalStyles }}>
          {this.props.i18n._('Log in')}
        </Button>
      </div>
    );

    return loginButton;
  }

  renderDefaultButtonOrder = () => [
    this.renderSignupButton('red', styles.leftButton),
    this.renderLoginButton('lightGrey'),
  ];

  renderLoginFlyoutEducation() {
    const { handleLoginError, showLoginEducationFlyout } = this.props;

    if (!showLoginEducationFlyout) {
      return null;
    }

    const CARET_SIZE = 25;

    let caretPositionStyles = {};
    if (this._loginButton) {
      const loginButtonWidth = this._loginButton.offsetWidth;
      const loginButtonOriginX = this._loginButton.offsetLeft;
      const caretOriginX = loginButtonOriginX + (loginButtonWidth - CARET_SIZE) / 2.0;
      caretPositionStyles = {
        height: String(CARET_SIZE) + 'px',
        width: String(CARET_SIZE) + 'px',
        left: caretOriginX,
      };
    }

    const caretShadow = (
      <div key="CaretShadow" style={{ ...styles.caret, ...styles.caretShadow, ...caretPositionStyles }} />
    );

    const caretMask = (
      <div key="CaretMask" style={{ ...styles.caret, ...caretPositionStyles }} />
    );

    const loginUpsell = (
      <div key="LoginUpsell" style={styles.loginUpsellPopup}>
        <LoginUpsellPopup
          handleLoginError={handleLoginError}
          key="loginUpsell"
          onClose={this.props.hideEducationFlyout}
        />
      </div>
    );

    return [
      caretShadow,
      loginUpsell,
      caretMask,
    ];
  }

  renderPersonalizedRightSection = () => {
    const continueString = StringUtil.safeFormat(this.props.i18n._('Continue as {{name}}'),
      { name: this.state.userInfo.first_name });
    return (<div>
      <div style={styles.profilePic}>
        <Touchable
          onTouch={(e) => { trackRegisterAction('unauth.login_button.click'); this.props.onLoginClick(e); }}>
          <Avatar src={this.state.userInfo.image_large_url} name={this.state.userInfo.first_name} />
        </Touchable>
      </div>
      <div style={styles.profilePicButtons}>
        <Touchable onTouch={(e) => { trackRegisterAction('unauth.login_button.click'); this.props.onLoginClick(e); }}>
          <div
            className="UnauthHeader__hoverUnderline"
            style={styles.continueLink}>
            {continueString}
          </div>
        </Touchable>
        <Touchable
          onTouch={(e) => { this.handleNotYouClick(e); }}>
          <div
            className="UnauthHeader__hoverUnderline"
            style={styles.notYouLink}>
            {this.props.i18n._('Not you?')}
          </div>
        </Touchable>
      </div>
    </div>);
  }

  renderRightContent = () => {
    if (this.state.headerStyle === 'personalized') {
      return this.renderPersonalizedRightSection();
    } else if (this.state.headerStyle === 'default') {
      return this.renderDefaultButtonOrder();
    } else {
      return null;
    }
  }

  render() {
    const { alignHeader, i18n } = this.props;

    const headerStyle = styles.header;
    const logoStyle = styles.logoContainer;
    const position = this.props.stickyHeader ? 'fixed' : 'static';
    const logoSize = 28;
    headerStyle.position = position;

    const headerProps = {};
    const tagline = i18n._('Pinterest');
    if (alignHeader) {
      headerProps.style = styles.alignedHeaderContainer;
    } else {
      headerProps.style = styles.headerContainer;
    }

    return (
      <div data-test-unauthHeader style={headerStyle}>
        <div {...headerProps}>
          <div style={styles.rightHeaderContent}>
            <div style={styles.barButtonsWrapper}>
              <div className="UnauthHeader__rightContentContainer" style={styles.rightContentContainer}>
                {this.renderRightContent()}
                {this.renderLoginFlyoutEducation()}
              </div>
            </div>
          </div>
          <div style={styles.leftHeaderContent}>
            <a href="/">
              <span style={logoStyle}>
                {logo(logoSize, false)}
              </span>
            </a>
            <div className={'UnauthHeader__discoverText'} style={styles.discoverText}>
              {tagline}
            </div>
            {this.props.children}
          </div>
        </div>
        {this.props.autocorrect}
      </div>
    );
  }
}

export default withI18n(UnauthHeader);

UnauthHeader.propTypes = {
  alignHeader: PropTypes.bool,
  autocorrect: PropTypes.element,
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.element),
    PropTypes.element,
  ]),
  handleLoginError: PropTypes.func,
  hideEducationFlyout: PropTypes.func,
  i18n: I18nPropType.isRequired,
  numServerRenderedPins: PropTypes.number,
  onLoginClick: PropTypes.func.isRequired,
  onSignupClick: PropTypes.func.isRequired,
  showLoginEducationFlyout: PropTypes.bool,
  stickyHeader: PropTypes.bool,
};

UnauthHeader.contextTypes = {
  isOpenExperience: PropTypes.bool.isRequired,
};

UnauthHeader.defaultProps = {
  stickyHeader: false,
};
