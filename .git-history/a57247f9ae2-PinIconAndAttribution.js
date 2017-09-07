/* eslint react/forbid-prop-types:0 */

import React, { Component, PropTypes } from 'react';
import { connect } from 'react-redux';
import * as StringUtil from 'app/common/lib/StringUtil.js';
import contextLog from 'app/common/redux/actions/contextLog';
import http2 from 'app/common/react/components/growth/unauth/lib/CDNUtils';
import Image from 'app/common/react/components/growth/unauth/Image/Image';
import withI18n, { I18nPropType } from 'app/common/lib/react/withI18n';

const styles = {
  richPinInfoWrapper: {
    overflow: 'hidden',
  },
  link: {
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
    overflow: 'hidden',
    cursor: 'auto',
    display: 'block',
    WebkitFontSmoothing: 'antialiased',
    MozOsxFontSmoothing: 'grayscale',
    paddingTop: '1px',
  },
  image: {
    position: 'static',
    height: '16px',
    width: '16px',
    borderRadius: '2px',
    verticalAlign: 'middle',
    border: '0px',
    display: 'inline-block',
  },
  wrapper: {
    margin: '7px 0 3px',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
    overflow: 'hidden',
    display: 'inline-block',
  },
  richAttribution: {
    color: '#aaa',
    fontWeight: 'normal',
    margin: '0 7px 0 7px',
  },
  attribution: {
    color: '#a7a7a7',
    fontWeight: 'bold',
    textDecoration: 'none',
    fontSize: '11px',
    margin: '0 7px 0 7px',
  },
  title: {
    clear: 'both',
    color: '#444',
    fontSize: 16,
    fontWeight: 'bold',
    margin: '0px',
    maxHeight: '76px',
    padding: '4px 0',
    WebkitFontSmoothing: 'antialiased',
  },
};

const renderFaviconPlaceholder = () => (<div style={styles.image} />);


const processRichSummary = (pin) => {
  const { rich_summary } = pin;
  let { apple_touch_icon_images: touchIcons, favicon_images: favicons } = rich_summary;
  touchIcons = touchIcons || {};
  favicons = favicons || {};

  return {
    faviconLink: touchIcons['50x'] || favicons['50x'] || touchIcons.orig || favicons.orig,
    siteName: rich_summary.site_name || pin.domain,
    title: rich_summary.display_name,
  };
};

const processPlaceInfo = (pin) => {
  const { place_summary } = pin;
  return {
    faviconLink: place_summary.source_icon,
    siteName: place_summary.source_name || pin.domain,
    title: place_summary.name,
  };
};

const detectAvailable = (pin) => {
  const { place_summary: placeSummary, rich_summary: richSummary } = pin;
  const hasRichSummary = richSummary && richSummary.type_name !== 'mobile application';
  const hasRichAttributionTitle = hasRichSummary && richSummary.display_name;
  const hasPlaceInfo = !!placeSummary;
  return {
    hasRichSummary,
    hasRichAttributionTitle,
    hasPlaceInfo,
  };
};

const calculatePinAttributionTitleNumLines = (title) => {
  let numLinesForTitle = 0;
  if (title) {
    const lineLength = 27;
    numLinesForTitle = Math.floor(title.length / lineLength) + 1;
    if (numLinesForTitle > 4) { numLinesForTitle = 4; }
  }
  return numLinesForTitle;
};

const calculatePinAttributionHeight = (pin, richPinPlacement) => {
  const { hasRichSummary, hasRichAttributionTitle, hasPlaceInfo } = detectAvailable(pin);
  let margin = 0;
  let title;
  let titleHeight = 0;
  let attributionHeight = 0;
  if (hasRichAttributionTitle) {
    margin = 8;
    attributionHeight = 0;
    title = processRichSummary(pin).title;
  } else if (hasPlaceInfo) {
    margin = 8;
    attributionHeight = 0;
    title = processPlaceInfo(pin).title;
  } else if (!!hasRichSummary || !!pin.attribution) {
    attributionHeight = 16;
  } else {
    return 0;
  }

  if (title) {
    const numLinesForTitle = calculatePinAttributionTitleNumLines(title);
    titleHeight = (19 * numLinesForTitle);
  }

  return margin + titleHeight + attributionHeight;
};

const trackClick = (e) => {
  this.props.dispatch(contextLog(PCONST.thrift.EventType.CLICK, {
    view: this.context.logging.viewType,
    viewParameter: this.context.logging.viewParameter,
    element: PCONST.thrift.ElementType.PIN_ATTRIBUTION,
    component: PCONST.thrift.ComponentType.FLOWED_PIN,
  }));
};

class PinIconAndAttribution extends Component {
  constructor(props) {
    super(props);
    this.state = {
      showFaviconImage: false,
    };
  }

  componentDidMount() {
    this.showFaviconTimeout = setTimeout(() => {
      this.setState({ showFaviconImage: true });
    }, 100);
  }

  componentWillUnmount() {
    clearTimeout(this.showFaviconTimeout);
  }

  renderRichPinInfo = (processedSummary) => {
    const numLinesForTitle = calculatePinAttributionTitleNumLines(processedSummary.title);
    return (
      <div style={styles.richPinInfoWrapper}>
        <h3
          className={'PinIconAndAttribution__title PinIconAndAttribution__' + numLinesForTitle + 'LineTitle'}
          style={styles.title}>{processedSummary.title}
        </h3>
      </div>
    );
  };

  renderRichPinSiteInfo = (processedSummary) => {
    const { siteName } = processedSummary;
    if (siteName) {
      return (
        <div style={styles.wrapper}>
          <Image
            alt={siteName}
            lazyLoad={false}
            renderPlaceholder={renderFaviconPlaceholder}
            src={http2(processedSummary.faviconLink)}
            style={styles.image}
            useBackgroundImage
          />
          <span style={styles.richAttribution}>
            {StringUtil.dangerouslyFormat(this.props.i18n._('from {{ rich_site_name }}'), { rich_site_name: siteName })}
          </span>
        </div>
      );
    }
    return undefined;
  };

  renderAttribution = (attribution) => {
    const { author_url, url, provider_favicon_url, author_name, rich_site_name, provider_name } = attribution;
    const link = author_url || url;
    const site_name = rich_site_name || provider_name;
    let faviconImage;
    if (provider_favicon_url) {
      faviconImage = (<Image
        alt={site_name}
        lazyLoad={false}
        renderPlaceholder={renderFaviconPlaceholder}
        src={http2(provider_favicon_url)}
        style={styles.image}
        useBackgroundImage
      />);
    }
    let attributionText;
    if (author_name) {
      attributionText = StringUtil.dangerouslyFormat(
        this.props.i18n._('by {{ author_name }}'), { author_name });
    } else {
      attributionText = StringUtil.dangerouslyFormat(
        this.props.i18n._('from {{ site_name }}'), { site_name });
    }

    return (
      <a href={link} onClick={trackClick}  rel="nofollow" style={styles.link} target="_blank" >
        {this.state.showFaviconImage ? faviconImage : null}
        <span style={styles.attribution}>
          {attributionText}
        </span>
      </a>
    );
  };

  render() {
    const { pin, richPinPlacement, pin: { rich_summary, domain } } = this.props;
    const hasRichSummary = rich_summary && rich_summary.type_name !== 'mobile application';
    const hasRichAttributionTitle = hasRichSummary && rich_summary.display_name;
    const hasPlaceInfo = !!pin.place_summary;
    if (richPinPlacement) {
      if (hasRichAttributionTitle) {
        return (<div>{this.renderRichPinInfo(processRichSummary(pin))}</div>);
      } else if (hasPlaceInfo) {
        return (<div>{this.renderRichPinInfo(processPlaceInfo(pin))}</div>);
      }
    } else if (!(hasRichAttributionTitle || hasPlaceInfo) && (hasRichSummary || pin.attribution)) {
      let attribution = pin.attribution;
      if (!attribution) {
        const processedSummary = processRichSummary(pin);
        attribution =  {
          author_url: '/source/' + domain + '/',
          rich_site_name: processedSummary.siteName,
          provider_favicon_url: processedSummary.faviconLink,
        };
      }
      return (<div>{this.renderAttribution(attribution)}</div>);
    }
    return (null);
  }
}

export { calculatePinAttributionHeight };

PinIconAndAttribution.propTypes = {
  dispatch: PropTypes.func.isRequired,
  i18n: I18nPropType.isRequired,
  pin: PropTypes.shape({
    id: PropTypes.string,
    attribution: PropTypes.object,
    domain: PropTypes.string.isRequired,
    place_summary: PropTypes.object,
    rich_summary: PropTypes.object,
  }),
  richPinPlacement: PropTypes.bool,
};

PinIconAndAttribution.contextTypes = {
  logging: PropTypes.shape({
    viewParameter: PropTypes.number,
    viewType: PropTypes.number.isRequired,
  }),
};

export default connect()(withI18n(PinIconAndAttribution));
