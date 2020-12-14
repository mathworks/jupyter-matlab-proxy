// Copyright 2020 The MathWorks, Inc.

import React from 'react';
import PropTypes from 'prop-types';
import './MatlabJsd.css';

function MatlabJsd({ url }) {
    return (
        <div id="MatlabJsd">
            <iframe
                title="MATLAB JSD"
                src={url}
                frameBorder="0"
                allowFullScreen />
        </div>
    );
}

MatlabJsd.propTypes = {
    url: PropTypes.string.isRequired
};

export default MatlabJsd;
