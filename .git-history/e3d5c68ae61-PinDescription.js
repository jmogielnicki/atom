/* eslint react/jsx-no-bind:0 */
/* eslint react/forbid-prop-types:0 */

import React, { Component, PropTypes } from 'react';
import DeepLink from 'app/common/react/components/growth/unauth/lib/Deeplink';
import DeeplinkRoutes from 'app/common/react/components/growth/unauth/lib/DeeplinkRoutes';
import urlUtil from 'app/common/lib/urlUtil';
import VaseCarousel from 'app/common/react/components/growth/unauth/pin/PinDescription/VaseCarousel';
import { track } from 'app/common/lib/react/analytics';
import withI18n, { I18nPropType } from 'app/common/lib/react/withI18n';
import withUnauthSeoExperiments, { ExperimentsPropType } from 'app/common/lib/react/withUnauthSeoExperiments';
import { smartTruncate, removeMultipleSpaces } from 'app/common/lib/react/strUtils';

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
    margin: '0 0 3px 0',
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

const computeTitle = pin => (pin.rich_summary && pin.rich_summary.display_name)
  || (pin.place_summary && pin.place_summary.name);

const getDescriptionAndAnnotations = (pin) => {
  const pinJoin = pin.pin_join || {};
  let visualAnnotations = pinJoin.visual_annotation;
  const visualDescriptions = pinJoin.visual_descriptions;
  const i18nVisualDescriptions = pinJoin.i18n_visual_descriptions;
  const hasVASE = !!(visualAnnotations || visualDescriptions || i18nVisualDescriptions);
  const title = computeTitle(pin);
  const descriptionEqualsTitle = pin.description && title &&
    pin.description.toLocaleLowerCase().trim() === title.toLocaleLowerCase().trim();
  let description = smartTruncate(pin.description || '', 496);
  const preferVASE = hasVASE && ((description && description.length < 3) || descriptionEqualsTitle);
  if (preferVASE) {
    if (visualDescriptions && visualDescriptions.length > 0) {
      description = visualDescriptions[0];
    } else if (i18nVisualDescriptions && i18nVisualDescriptions.length > 0) {
      description = i18nVisualDescriptions[0];
    } else {
      description = visualAnnotations + ' ';
      visualAnnotations = null;
    }
  }

  const trimmedDesc = description.replace(/\s+/g, ' ').trim();
  return { description: trimmedDesc, visualAnnotations };
};

const calculateDescriptionNumLines = (description) => {
  description = removeMultipleSpaces(description);
  const lineLength = 34;
  return Math.floor(description.length / lineLength) + 1;
};

const fetchDescriptions = (pinJoin) => {
  if (pinJoin.visual_descriptions && pinJoin.visual_descriptions.length > 0) {
    return pinJoin.visual_descriptions;
  } else if (pinJoin.i18n_visual_descriptions && pinJoin.i18n_visual_descriptions.length > 0) {
    return pinJoin.i18n_visual_descriptions;
  }
  return undefined;
};

const calculatePinDescriptionHeight = (pin) => {
  const { description } = getDescriptionAndAnnotations(pin);
  const margin = 10;
  const lineHeight = 17;
  let height = 0;
  const pinJoin = pin.pin_join || {};
  const vaseDescriptions = fetchDescriptions(pinJoin);
  if (!!vaseDescriptions && vaseDescriptions.length > 0) {
    const seeMoreButtonHeight = 18;
    height += seeMoreButtonHeight;
  } else {
    // hack for experiment only - due to the way the pin meta margins overlap
    height -= 5;
  }
  const visualAnnotations = pinJoin.visual_annotation;
  if (!!visualAnnotations && visualAnnotations.length > 0) {
    const carouselHeight = 30;
    height += carouselHeight;
  }
  if (description) {
    const numLinesForDescription = calculateDescriptionNumLines(description);
    height += margin + (lineHeight * numLinesForDescription);
  }
  return height;
};

export class PinDescription extends Component {
  getVaseTagsGroup() {
    const seoUnauthExperiments = this.props.seoUnauthExperiments;
    const pageType = this.context.pageType;

    if (pageType === 'board') {
      return seoUnauthExperiments.v2ActivateExperiment('vase_relaunch_board');
    } else if (pageType === 'pin') {
      return seoUnauthExperiments.v2ActivateExperiment('vase_relaunch_pin');
    } else if (pageType === 'klp') {
      return seoUnauthExperiments.v2ActivateExperiment('vase_relaunch_explore');
    } else {
      return undefined;
    }
  }

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

  handleSeeMoreClick(e) {
    this.props.vaseClickHandler(this.props.pin);
    e.stopPropagation();
  }

  // TODO Refactor repetitive deeplink logic for components in pin level
  handleTagClick(interestName, e) {
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
    if (deepLink.shouldDeepLink(document.referrer, this.context.userAgent, false, this.context.isAndroidLite)) {
      e.preventDefault();
      deepLink.navigateToDeepLink(this.context.unauthId,
        DeeplinkRoutes.buildExploreDeeplinks(interestName));
    }
    e.stopPropagation();
  }

  useVaseCarousel() {
    const vaseTagsGrp = this.getVaseTagsGroup();
    const isMobile = this.context.userAgent.isMobile;

    if (vaseTagsGrp === 'control') {
      return false;
    } else if (isMobile && vaseTagsGrp === 'enabled_hidden_mobile') {
      return false;
    } else if (vaseTagsGrp === 'enabled') {
      return true;
    }

    // Unless group is enabled, use the old treatment instead of the VASE
    // carousel for non-en-* locales until we improve non-English tags
    return this.context.locale.startsWith('en-');
  }

  hideDescription() {
    return this.context.userAgent.isMobile;
  }

  formatCookTime(time) {
    const i18n = this.props.i18n;
    const { h, m } = time;

    if (h > 0) {
      let hours = h;
      if (m > 45) {
        hours += 1;
      } else if (m > 15) {
        hours += 0.5;
      }
      const label = i18n.ngettext('hr', 'hrs', hours, '{{count}} {{hrs}}');
      return `${hours} ${label}`;
    } else {
      const label = i18n.ngettext('min', 'mins', m, '{{ count }} {{ mins }}');
      return `${m} ${label}`;
    }
  }

  renderDescription(description) {
    if (description) {
      if (this.hideDescription() && this.getVaseTagsGroup() === 'enabled_hidden_description') {
        // description will be rendered as part of VASE hidden texts
        return undefined;
      }

      const numLinesForDescription = calculateDescriptionNumLines(description);
      const style = this.hideDescription() ? { ...styles.description, ...styles.hidden } : styles.description;
      return (
        <p
          className={'PinDescription__desc PinDescription__' + numLinesForDescription + 'LineDesc'}
          data-test-desc
          style={style}>
          {description}
        </p>
      );
    }
    return undefined;
  }

  renderCarousel(annoations) {
    return (<VaseCarousel
      tagClickHandler={this.handleTagClick.bind(this)}
      visualAnnotations={annoations}
    />);
  }

  renderDiets(diets) {
    const tags = diets.map(diet => (
      diet.split(/\s+/).map(d => d[0].toUpperCase() + d.substring(1)).join(' ')
    ));
    return (
      <h4>{tags.join(' ')}</h4>
    );
  }

  renderCookTimes(cook_times) {
    return ['prep', 'cook', 'total'].map((key) => {
      if (cook_times[key]) {
        const label = key[0].toUpperCase() + key.substring(1) + ' Time';
        return (
          <h4>{label}: {this.formatCookTime(cook_times[key])}</h4>
        );
      } else {
        return null;
      }
    }).filter(Boolean);
  }

  renderIngredients(categorized_ingredients) {
    return (
      <div>
        {categorized_ingredients.map(category => (
          <div>
            <h4 key={category.id}>{category.category}</h4>
            <ul>
              {category.ingredients.map(ingredient => (
                <li key={ingredient.id}>{ingredient.amt} {ingredient.name}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    );
  }

  renderRecipe(recipe) {
    if (!this.props.pin.expandedVASE && !this.context.isBot) {
      return null;
    }

    const vaseRecipeGroup = this.getVaseRecipeGroup();
    if (!vaseRecipeGroup || vaseRecipeGroup.startsWith('control')) {
      return null;
    }

    const { categorized_ingredients, cook_times, diets, servings_summary } = recipe;

    const divStyle = this.props.pin.expandedVASE ? styles.recipe : { ...styles.hidden, ...styles.recipe };

    return (
      <div data-test-desc-recipe style={divStyle}>
        {diets && diets.length > 0 && this.renderDiets(diets)}
        {cook_times && this.renderCookTimes(cook_times)}
        {categorized_ingredients && categorized_ingredients.length > 0
           && this.renderIngredients(categorized_ingredients)
        }
        {servings_summary && servings_summary.summary
          && (<h4>{servings_summary.summary}</h4>)
        }
      </div>
    );
  }

  renderHiddenDescriptions(annotations, description, vaseTexts) {
    // For regular users do not include hidden texts in DOM
    if (!this.props.pin.expandedVASE && !this.context.isBot) {
      return null;
    }

    const vaseRecipeGroup = this.getVaseRecipeGroup();
    if (vaseRecipeGroup && vaseRecipeGroup === 'enabled_replace_text') {
      return null;
    }

    const textStyle = this.props.pin.expandedVASE ? styles.vaseText : { ...styles.vaseText, ...styles.hidden };

    const markupList = [];

    // when carousel is enabled, omit tags/annotations from hidden description
    if (!this.useVaseCarousel() && annotations && annotations.length > 0) {
      markupList.push((
        <h4 key="tags" data-test-vaseTags style={textStyle}>{annotations.join(', ')}</h4>
      ));
    }

    if (this.getVaseTagsGroup() === 'enabled_hidden_description') {
      if (this.hideDescription() && description) {
        markupList.push((
          <h4 key="desc" data-test-desc style={textStyle}>{description}</h4>
        ));
      }
    }

    if (vaseTexts && vaseTexts.length > 0) {
      markupList.push(...vaseTexts.map((text, index) => (
        <h4 key={`vase-${index}`} data-test-vaseDesc style={textStyle}>{text}</h4>
      )));
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
    const { pin } = this.props;

    const pinJoin = this.props.pin.pin_join || {};
    let vaseAnnotations = pinJoin.visual_annotation;
    let vaseDescriptions = fetchDescriptions(pinJoin);

    // We create functions for these flags because they can be changed below.
    const hasVaseDescriptions = () => !!vaseDescriptions && vaseDescriptions.length > 0;
    const hasVaseAnnotations = () => !!vaseAnnotations && vaseAnnotations.length > 0;

    const title = computeTitle(pin);
    const descriptionEqualsTitle = pin.description && title &&
      pin.description.toLocaleLowerCase().trim() === title.toLocaleLowerCase().trim();
    let description = removeMultipleSpaces(smartTruncate(pin.description || '', 496));

    // Use the first VASE description if main description too short, or redundant
    if ((description && description.length < 3) || descriptionEqualsTitle) {
      if (hasVaseDescriptions()) {
        description = vaseDescriptions[0];
        vaseDescriptions = vaseDescriptions.slice(1);
      } else if (hasVaseAnnotations()) {
        description = vaseAnnotations.toString();
        vaseAnnotations = null;
      } else {
        description = null;
      }
    }

    const useVaseCarousel = this.useVaseCarousel();
    const hideDescription = this.hideDescription();

    const vaseDescriptionsMarkup = this.renderHiddenDescriptions(
      vaseAnnotations, description, vaseDescriptions);

    // if there is no hidden markup, don't show the 'See More' link
    let buttons = null;
    if ((vaseDescriptions && vaseDescriptions.length > 0) ||
        (hideDescription && description) ||
        (!useVaseCarousel && vaseAnnotations && vaseAnnotations.length > 0)
    ) {
      buttons = this.renderSeeMore();
    }

    const recipe = pin.rich_metadata && pin.rich_metadata.recipe;

    return (
      <div>
        {(useVaseCarousel && vaseDescriptions) ? this.renderCarousel(vaseAnnotations) : null}
        {this.renderDescription(description)}
        {recipe ? this.renderRecipe(recipe) : null}
        {vaseDescriptionsMarkup}
        {buttons}
      </div>
    );
  }
}

export { calculatePinDescriptionHeight };

PinDescription.propTypes = {
  i18n: I18nPropType.isRequired,
  pin: PropTypes.shape({
    id: PropTypes.string,
    description: PropTypes.string.isRequired,
    expandedVASE: PropTypes.boolean,
    image_signature: PropTypes.string,
    place_summary: PropTypes.object,
    pin_join: PropTypes.object,
    rich_metadata: PropTypes.object,
    rich_summary: PropTypes.object,
  }),
  seoUnauthExperiments: ExperimentsPropType,
  title: PropTypes.string,
  vaseClickHandler: PropTypes.func.isRequired,
};

PinDescription.contextTypes = {
  country: PropTypes.string,
  currentUrl: PropTypes.string,
  isAndroidLite: PropTypes.bool.isRequired,
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
