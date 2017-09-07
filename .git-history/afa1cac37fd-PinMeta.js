/* eslint react/forbid-prop-types:0 */

import React, { PropTypes } from 'react';
import PinDescription, { calculatePinDescriptionHeight } from 'app/common/react/components/growth/unauth/pin/PinDescription/PinDescription';
import PinIconAndAttribution, { calculatePinAttributionHeight } from 'app/common/react/components/growth/unauth/pin/PinIconAndAttribution/PinIconAndAttribution';

const styles = {
  wrapper: {
    padding: '5px 8px',
  },
};

const calculatePinMetaHeight = (pin, locale) => {
  const margin = 10;
  const descriptionHeight = calculatePinDescriptionHeight(pin);
  const pinAttribution = calculatePinAttributionHeight(pin, true);

  return descriptionHeight +
    pinAttribution +
    margin;
};

export default function PinMeta(props) {
  const { hideMeta, pin } = props;
  if (hideMeta) {
    if (pin.has_required_attribution_provider) {
      return (
        <div style={styles.wrapper}>
          <PinIconAndAttribution
            pin={pin}
          />
        </div>
      );
    }
    return null;
  }
  return (
    <div style={styles.wrapper}>
      <PinIconAndAttribution
        pin={pin}
        richPinPlacement
      />
      <PinDescription
        pin={pin}
        vaseClickHandler={props.vaseClickHandler}
      />
      <PinIconAndAttribution
        pin={pin}
      />
    </div>
  );
}

export { calculatePinMetaHeight };

PinMeta.propTypes = {
  hideMeta: PropTypes.bool,
  pin: PropTypes.shape({
    id: PropTypes.string,
    aggregated_pin_data: PropTypes.object,
    attribution: PropTypes.object,
    comment_count: PropTypes.number.isRequired,
    description: PropTypes.string.isRequired,
    domain: PropTypes.string.isRequired,
    like_count: PropTypes.number.isRequired,
    pin_join: PropTypes.object,
    place_summary: PropTypes.object,
    repin_count: PropTypes.number.isRequired,
    rich_summary: PropTypes.object,
  }),
  vaseClickHandler: PropTypes.func.isRequired,
};
