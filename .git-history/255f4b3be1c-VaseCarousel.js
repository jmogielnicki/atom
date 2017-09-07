/* eslint react/jsx-no-bind:0 */

import React, { Component, PropTypes } from 'react';
import { getPinMeasurements } from 'app/common/react/components/growth/unauth/pin/pinUtils.js';
import { Icon } from 'gestalt';
import withI18n, { I18nPropType } from 'app/common/lib/react/withI18n';

const RIGHT = 'RIGHT';
const LEFT = 'LEFT';
const pinMeasurements = getPinMeasurements();

const styles = {
  gradientLeft: {
    display: 'block',
    background: '-webkit-linear-gradient(left, rgba(255,255,255,1) 25%,rgba(255,255,255,0) 100%)',
    height: '30px',
    left: '0px',
    top: '0px',
    position: 'absolute',
    width: '45px',
    lineHeight: '25px',
    paddingLeft: '4px',
    paddingTop: '2px',
  },
  gradientRight: {
    background: '-webkit-linear-gradient(right, rgba(255,255,255,1) 25%,rgba(255,255,255,0) 100%)',
    height: '30px',
    right: '0px',
    top: '0px',
    position: 'absolute',
    width: '45px',
    textAlign: 'right',
    lineHeight: '25px',
    paddingRight: '4px',
    paddingTop: '2px',
  },
  carouselWrapper: {
    overflow: 'scroll',
    whiteSpace: 'nowrap',
    padding: '3px 0 22px 0',
  },
  carouselContainer: {
    height: pinMeasurements.vaseCarouselHeight + 'px',
    overflow: 'hidden',
    position: 'relative',
  },
  carouselTag: {
    backgroundColor: '#ebebe8',
    borderRadius: '5px',
    color: '#555',
    display: 'inline-block',
    fontSize: '9px',
    fontWeight: 'bold',
    margin: '0 5px 0 0',
    padding: '7px 7px',
    whiteSpace: 'nowrap',
    wordWrap: 'break-word',
  },
  h4: {
    display: 'inline-block',
  },
};

class VaseCarousel extends Component {
  constructor() {
    super();
    this.state = {
      scrollTo: 0,
      scrollMin: true,
      scrollMax: false,
    };
  }

  componentDidMount() {
    this.wrapper.addEventListener('scroll', this.handleScroll.bind(this));
  }

  componentDidUpdate() {
    this.wrapper.scrollLeft = this.state.scrollTo;
  }

  componentWillUnmount() {
    this.wrapper.removeEventListener('scroll', this.handleScroll.bind(this));
  }

  handleScroll() {
    // need to round scrollLeft, or it doesn't line up with bounds when zoomed
    const scrollLeft = Math.round(this.wrapper.scrollLeft);
    const scrollRight = scrollLeft + this.wrapper.clientWidth;

    const scrollMin = scrollLeft === 0;
    const scrollMax = scrollRight >= this.wrapper.scrollWidth;

    const scrollTo = scrollLeft;
    this.setState({ scrollTo, scrollMin, scrollMax });
  }

  handleArrowClick(direction, event) {
    event.preventDefault();
    event.stopPropagation();

    // extra spacing due to margin + padding of the tag bubble
    const spacingLeft = 12;
    const getTagOffset = el => (el.offsetLeft - spacingLeft);

    // need to round scrollLeft, or it doesn't line up with bounds when zoomed
    const currentScrollOffset = Math.round(this.wrapper.scrollLeft);
    const tagOffsets = this.tags.map(getTagOffset);

    // add some "wiggle" room to our calculation
    const wiggle = 4;
    let offset;
    if (direction === RIGHT) {
      // scroll right: find first edge that is greater than current scroll
      // position and scroll to it.
      offset = tagOffsets.find(tagOffset => tagOffset > currentScrollOffset + wiggle);
    } else if (direction === LEFT) {
      // scroll left: find last edge that is less than current scroll position
      // and scroll to it.
      offset = tagOffsets.reverse().find(tagOffset => tagOffset < currentScrollOffset - wiggle);
    }

    this.setState({
      scrollTo: offset,
    });
  }

  renderTags() {
    // ref callback to generate list of tags ...
    const appendTagRef = (index, el) => {
      if (typeof this.tags === 'undefined') {
        this.tags = [];
      }
      this.tags[index] = el;
    };

    const { markupTagGroup } = this.props;
    if (markupTagGroup && (markupTagGroup.startsWith('enabled_all') || markupTagGroup.startsWith('enabled_tokens'))) {
      return this.props.visualAnnotations.map((annotation, index) => (
        <h4 style={styles.h4}>
          <a
            href={'/explore/' + encodeURIComponent(annotation.replace(/[\s\/\\]+/g, '-').toLowerCase()) + '/'}
            key={index}
            onClick={this.props.tagClickHandler.bind(null, annotation)}
            ref={appendTagRef.bind(this, index)}
            role="contentinfo"
            style={styles.carouselTag}
            target="_blank">
            {annotation}
          </a>
        </h4>
      ));
    } else {
      return this.props.visualAnnotations.map((annotation, index) => (
        <a
          href={'/explore/' + encodeURIComponent(annotation.replace(/[\s\/\\]+/g, '-').toLowerCase()) + '/'}
          key={index}
          onClick={this.props.tagClickHandler.bind(null, annotation)}
          ref={appendTagRef.bind(this, index)}
          role="contentinfo"
          style={styles.carouselTag}
          target="_blank">
          {annotation}
        </a>
      ));
    }
  }

  render() {
    return (
      <div style={styles.carouselContainer} data-test-vaseTags>
        <div
          ref={(el) => { this.wrapper = el; }}
          style={styles.carouselWrapper}>
          {this.renderTags()}
          {this.state.scrollMin ? null : (
            <a
              href="javascript:void(0);"
              onClick={this.handleArrowClick.bind(this, LEFT)}
              style={styles.gradientLeft}>
              <Icon
                accessibilityLabel={this.props.i18n._('Back', 'Accessible label for the carousel back icon')}
                icon="arrow-back"
                inline
                size={8}
              />
            </a>
          )}
          {this.state.scrollMax ? null : (
            <a
              href="javascript:void(0);"
              onClick={this.handleArrowClick.bind(this, RIGHT)}
              style={styles.gradientRight}>
              <Icon
                accessibilityLabel={this.props.i18n._('Forward', 'Accessible label for the carousel forward icon')}
                icon="arrow-forward"
                inline
                size={8}
              />
            </a>
          )}
        </div>
      </div>
    );
  }
}

VaseCarousel.propTypes = {
  i18n: I18nPropType.isRequired,
  markupTagGroup: PropTypes.string,
  tagClickHandler: PropTypes.func.isRequired,
  visualAnnotations: PropTypes.arrayOf(PropTypes.string).isRequired,
};

VaseCarousel.contextTypes = {
  pageType: PropTypes.string.isRequired,
};

export default withI18n(VaseCarousel);
