// Copyright 2020 The MathWorks, Inc.

import React from 'react';
import PropTypes from 'prop-types';
import Linkify from 'react-linkify';
import './Error.css';

function Error({message, logs, children}) {

    const logReport = logs
        ? (
            <p className="error-msg">
                {logs}
            </p>
        )
        : null;

    return (
        <div className="modal show"
            id="error"
            tabIndex="-1"
            role="dialog"
            aria-labelledby="help-dialog-title">
            <div className="modal-dialog modal-dialog-centered" role="document">
                <div className="modal-content alert alert-danger">
                    <div className="modal-header">
                        <span className={`alert_icon icon-alert-error`}></span>
                        <h4 className="modal-title alert_heading">Error</h4>
                    </div>
                    <div className="modal-body">
                        <p>{message}</p>
                        <Linkify>{logReport}</Linkify>
                        {children}
                    </div>
                </div>
            </div>
        </div>
    );
};

Error.propTypes = {
    message: PropTypes.string.isRequired,
    logs: PropTypes.arrayOf(PropTypes.string),
    children: PropTypes.node
};

export default Error;
