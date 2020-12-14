// Copyright 2020 The MathWorks, Inc.

import React from 'react';
import PropTypes from 'prop-types';
import './Overlay.css';

function Overlay({
    children,
    transparent=false
}) {

    return (
        <div
            id="overlay"
            style={
                {
                    backgroundColor: transparent ? "transparent" : null
                }
            }
        >
            {children}
        </div>
    );
}

Overlay.propTypes = {
    transparent: PropTypes.bool
};

export default Overlay;
