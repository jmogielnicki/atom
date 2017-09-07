/* eslint react/jsx-no-bind:0 */
/* eslint react/forbid-prop-types:0 */
// @flow

import React, { Component, PropTypes } from 'react';
import DeepLink from 'app/common/react/components/growth/unauth/lib/Deeplink';
import DeeplinkRoutes from 'app/common/react/components/growth/unauth/lib/DeeplinkRoutes';
import Recipe from 'app/common/react/components/growth/unauth/pin/Recipe/Recipe';
import type ExperimentsClient from 'app/common/lib/ExperimentsClient';
import type { I18nType } from 'app/common/lib/i18n';
import urlUtil from 'app/common/lib/urlUtil';
import VaseCarousel from 'app/common/react/components/growth/unauth/pin/PinDescription/VaseCarousel';
import { interpolateNamedTemplate }  from 'app/common/lib/react/interpolate';
import { track } from 'app/common/lib/react/analytics';
import type { VaseAnnotations, PinType } from 'app/common/react/components/growth/unauth/lib/PropTypes';
import withI18n, { I18nPropType } from 'app/common/lib/react/withI18n';
import withUnauthSeoExperiments, { ExperimentsPropType } from 'app/common/lib/react/withUnauthSeoExperiments';
import { getPinMeasurements, shouldUseVaseCarousel, shouldRenderDescription, getDescriptionAndAnnotations,
  calculateDescriptionNumLines, shouldRenderSeeMore, hideDescription, getVaseTagsGroup }
  from 'app/common/react/components/growth/unauth/pin/pinUtils';

type Context = {
  country: string,
  currentUrl: string,
  isBot: boolean,
  locale: string,
  pageType: string,
  userAgent: {
    canUseNativeApp: boolean,
    isMobile: boolean,
    isTablet: boolean,
    platform: string,
    platformVersion: Array<number>,
    raw: string,
  },
};

type Props = {
  i18n: I18nType,
  pin: PinType,
  seoUnauthExperiments: ExperimentsClient,
  vaseClickHandler: (pin: PinType) => void,
};

const pinMeasurements = getPinMeasurements();

const styles = {
  description: {
    margin: '5px 0',
    padding: '0px',
    WebkitFontSmoothing: 'antialiased',
    MozOsxFontSmoothing: 'grayscale',
    color: '#333',
    fontSize: 13,
    lineHeight: '17px',
    wordWrap: 'break-word',
  },
  hidden: {
    display: 'none',
  },
  recipe: {
    color: '#333',
    fontSize: 11,
    margin: '5px 0',
    padding: '0px',
    MozOsxFontSmoothing: 'grayscale',
    WebkitFontSmoothing: 'antialiased',
    wordWrap: 'break-word',
  },
  seeMoreLink: {
    backgroundColor: 'transparent',
    border: 0,
    color: '#555',
    fontSize: '12px',
    fontWeight: 'bold',
    height: pinMeasurements.seeMoreButtonHeight + 'px',
    margin: '0 0 ' + pinMeasurements.seeMoreButtonBottomMargin + 'px 0',
    MozOsxFontSmoothing: 'grayscale',
    outline: 'none',
    padding: 0,
    WebkitFontSmoothing: 'antialiased',
  },
  vaseText: {
    color: '#999',
    fontSize: '9px',
    fontWeight: 'normal',
    margin: '5px 0',
    wordWrap: 'break-word',
  },
};

export class PinDescription extends Component<void, Props, void> {
  getVaseRecipeGroup() {
    // don't use recipe experiment if pin is not a recipe
    const rich_metadata = this.props.pin.rich_metadata;
    if (rich_metadata && !rich_metadata.recipe) {
      return undefined;
    }

    const seoUnauthExperiments = this.props.seoUnauthExperiments;
    const pageType = this.context.pageType;

    if (pageType === 'board') {
      return seoUnauthExperiments.v2ActivateExperiment('vase_recipe_board');
    } else if (pageType === 'pin') {
      return seoUnauthExperiments.v2ActivateExperiment('vase_recipe_pin');
    } else if (pageType === 'klp') {
      return seoUnauthExperiments.v2ActivateExperiment('vase_recipe_explore');
    } else {
      return undefined;
    }
  }

  getMarkupTagGroup() {
    const seoUnauthExperiments = this.props.seoUnauthExperiments;
    const pageType = this.context.pageType;

    if (pageType === 'board') {
      return seoUnauthExperiments.v2ActivateExperiment('markup_tag_board');
    } else if (pageType === 'pin') {
      return seoUnauthExperiments.v2ActivateExperiment('markup_tag_pin');
    } else if (pageType === 'klp') {
      return seoUnauthExperiments.v2ActivateExperiment('markup_tag_explore');
    } else {
      return undefined;
    }
  }

  context: Context;

  handleSeeMoreClick(e: SyntheticEvent) {
    this.props.vaseClickHandler(this.props.pin);
    e.stopPropagation();
  }

  handleBoardLinkClick(e: SyntheticEvent) {
    e.stopPropagation();
  }

  // TODO Refactor repetitive deeplink logic for components in pin level
  handleTagClick(interestName: string, e: SyntheticEvent) {
    const { currentUrl, pageType } = this.context;

    track(PCONST.thrift.EventType.CLICK, {
      element: PCONST.thrift.ElementType.VASE_TAG,
      component: PCONST.thrift.ComponentType.VASE_TAGS_WRAPPER,
      unauth_vase_tag: interestName,
      unauth_vase_tag_image_sig: this.props.pin.image_signature,
      unauth_page_type: pageType,
      unauth_page_id: urlUtil.getUnauthPageId(pageType, currentUrl),
    });
    const deepLink = new DeepLink(this.props.seoUnauthExperiments,
      this.context.userAgent.raw,
      this.context.userAgent.platform,
      this.context.userAgent.platformVersion);
    if (deepLink.shouldDeepLink(document.referrer, this.context.userAgent, false)) {
      e.preventDefault();
      // $FlowIssue: unauthId was never specified in the contextTypes. How can it be set?
      deepLink.navigateToDeepLink(this.context.unauthId,
        DeeplinkRoutes.buildExploreDeeplinks(interestName));
    }
    e.stopPropagation();
  }

  shouldRenderRecipe(pin: PinType) {
    const recipe = pin.rich_metadata && pin.rich_metadata.recipe;
    if (!recipe) {
      return null;
    }
    const vaseRecipeGroup = this.getVaseRecipeGroup();
    if (!vaseRecipeGroup || vaseRecipeGroup.startsWith('control')) {
      return null;
    }
    if (!pin.expandedVASE && !this.context.isBot) {
      return null;
    }
    return recipe;
  }

  renderDescription(description: string, isMobile: boolean) {
    const numLinesForDescription = calculateDescriptionNumLines(description);
    const style = hideDescription(isMobile) ? { ...styles.description, ...styles.hidden } : styles.description;
    return (
      <p
        className={'PinDescription__desc PinDescription__' + numLinesForDescription + 'LineDesc'}
        data-test-desc
        style={style}>
        {description}
      </p>
    );
  }

  renderCarousel(annoations: VaseAnnotations) {
    return (<VaseCarousel
      markupTagGroup={this.getMarkupTagGroup()}
      tagClickHandler={this.handleTagClick.bind(this)}
      visualAnnotations={annoations}
    />);
  }

  renderRecipe(pin: PinType) {
    return (<Recipe
      pin={pin}
    />);
  }

  renderHiddenDescriptions(
    annotations: ?VaseAnnotations,
    description: ?string,
    vaseTexts: ?Array<string>,
    seoUnauthExperiments: ExperimentsClient,
    context: Context,
  ) {
    let useDifferentTags = false;
    const markupTagGroup = this.getMarkupTagGroup();
    if (markupTagGroup &&
      (markupTagGroup.startsWith('enabled_all') || markupTagGroup.startsWith('enabled_description'))) {
      useDifferentTags = true;
    }

    // For regular users do not include hidden texts in DOM
    if (!this.props.pin.expandedVASE && !context.isBot) {
      return null;
    }

    const vaseRecipeGroup = this.getVaseRecipeGroup();
    if (vaseRecipeGroup && vaseRecipeGroup === 'enabled_replace_text') {
      return null;
    }

    const textStyle = this.props.pin.expandedVASE ? styles.vaseText : { ...styles.vaseText, ...styles.hidden };
    const markupList = [];

    // when carousel is enabled, omit tags/annotations from hidden description
    if (!shouldUseVaseCarousel(seoUnauthExperiments, context, vaseTexts, annotations)) {
      let vaseTags = (<h4 key="tags" data-test-vaseTags style={textStyle}>{annotations.join(', ')}</h4>);
      if (useDifferentTags) {
        vaseTags = (<h3 key="tags" data-test-vaseTags style={textStyle}>{annotations.join(', ')}</h3>);
      }
      markupList.push(vaseTags);
    }

    if (getVaseTagsGroup(seoUnauthExperiments, context) === 'enabled_hidden_description') {
      if (hideDescription(context.userAgent.isMobile) && description) {
        let vaseDesc = (<h4 key="desc" data-test-desc style={textStyle}>{description}</h4>);
        if (useDifferentTags) {
          vaseDesc = (<h3 key="desc" data-test-desc style={textStyle}>{description}</h3>);
        }
        markupList.push(vaseDesc);
      }
    }

    if (vaseTexts && vaseTexts.length > 0) {
      const { pin: { board, in_board_backlinks_exp, max_vase_descriptions } } = this.props;

      if (in_board_backlinks_exp) {
        // Remove last VASE description if we have the max amount
        if (vaseTexts.length === max_vase_descriptions) {
          vaseTexts.pop();
        }

        // Add board backlink
        if (in_board_backlinks_exp) {
          const i18n = this.props.i18n;
          const clickHandler = this.handleBoardLinkClick.bind(this);
          const boardAttribution = interpolateNamedTemplate(
            i18n._('Find this Pin and more on {{ board_link }}.', 'Link to pin\'s board'),
            { board_link: <a href={board.url} key="board-link" onClick={clickHandler} target="_blank">
              {board.name}</a> },
          );
          markupList.push((
            <h4 key="board-attribution" style={textStyle}>{boardAttribution}</h4>
          ));
        }
      }

      if (useDifferentTags) {
        markupList.push(...vaseTexts.map((text, index) => (
          <h3 key={`vase-${index}`} data-test-vaseDesc style={textStyle}>{text}</h3>
        )));
      } else {
        markupList.push(...vaseTexts.map((text, index) => (
          <h4 key={`vase-${index}`} data-test-vaseDesc style={textStyle}>{text}</h4>
        )));
      }
    }
    return markupList;
  }

  renderSeeMore() {
    const clickHandler = this.handleSeeMoreClick.bind(this);
    const i18n = this.props.i18n;

    let text = this.props.pin.expandedVASE ? i18n._('See Less') : i18n._('See More');

    const vaseRecipeGroup = this.getVaseRecipeGroup();
    if (vaseRecipeGroup && vaseRecipeGroup === 'enabled_replace_text') {
      text = this.props.pin.expandedVASE ? i18n._('Hide Recipe') : i18n._('Show Recipe');
    }

    return (<button onClick={clickHandler} style={styles.seeMoreLink}>{text}</button>);
  }

  render() {
    // Note: any logic that would changes the height of any part of the pin that is visible on pageload
    // should be added to methods in pinUtils.js so that it can be used to measure height of pin on server
    const { pin } = this.props;
    const seoUnauthExperiments = this.props.seoUnauthExperiments;
    const isMobile = this.context.userAgent.isMobile;
    const { description, vaseAnnotations, vaseDescriptions } = getDescriptionAndAnnotations(pin);
    const vaseDescriptionsMarkup = this.renderHiddenDescriptions(
      vaseAnnotations, description, vaseDescriptions, seoUnauthExperiments, this.context);
    return (
      <div>
        {shouldUseVaseCarousel(seoUnauthExperiments, this.context, vaseDescriptions, vaseAnnotations) ?
          this.renderCarousel(vaseAnnotations) : null}
        {shouldRenderDescription(description, seoUnauthExperiments, this.context) ?
          this.renderDescription(description, isMobile) : null}
        {this.shouldRenderRecipe(pin) ? this.renderRecipe(pin) : null}
        {vaseDescriptionsMarkup}
        {shouldRenderSeeMore(vaseDescriptions, description, vaseAnnotations, this.context,
          seoUnauthExperiments) ? this.renderSeeMore() : null}
      </div>
    );
  }
}


PinDescription.propTypes = {
  i18n: I18nPropType.isRequired,
  pin: PropTypes.shape({
    board: PropTypes.shape({
      name: PropTypes.string,
      url: PropTypes.string,
    }),
    id: PropTypes.string,
    description: PropTypes.string.isRequired,
    expandedVASE: PropTypes.bool,
    image_signature: PropTypes.string,
    in_board_backlinks_exp: PropTypes.bool,
    max_vase_descriptions: PropTypes.number,
    place_summary: PropTypes.object,
    pin_join: PropTypes.object,
    rich_metadata: PropTypes.object,
    rich_summary: PropTypes.object,
  }),
  seoUnauthExperiments: ExperimentsPropType,
  vaseClickHandler: PropTypes.func.isRequired,
};

PinDescription.contextTypes = {
  country: PropTypes.string,
  currentUrl: PropTypes.string,
  isBot: PropTypes.bool.isRequired,
  locale: PropTypes.string.isRequired,
  pageType: PropTypes.string.isRequired,
  userAgent: PropTypes.shape({
    canUseNativeApp: PropTypes.bool.isRequired,
    isMobile: PropTypes.bool.isRequired,
    isTablet: PropTypes.bool.isRequired,
    platform: PropTypes.string.isRequired,
    platformVersion: PropTypes.arrayOf(PropTypes.number),
    raw: PropTypes.string.isRequired,
  }).isRequired,
};

export default withUnauthSeoExperiments(withI18n(PinDescription));
