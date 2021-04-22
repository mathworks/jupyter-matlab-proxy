// Copyright 2020-2021 The MathWorks, Inc.

import React from 'react';
import { useSelector } from 'react-redux';
import PropTypes from 'prop-types';
import './Help.css';

import {
    selectOverlayHidable
} from '../../selectors';

function Help({
    closeHandler,
    dismissAllHandler
}) {
    const overlayHidable = useSelector(selectOverlayHidable);

    const onCloseClick = event => {
        if(event.target === event.currentTarget) {
            event.preventDefault();
            dismissAllHandler();
        }
    };

    const url = 'https://github.com/mathworks/jupyter-matlab-proxy/blob/main/README.md';

    return (
        <div className="modal show"
            id="help"
            onClick={overlayHidable ? onCloseClick : null}
            tabIndex="-1"
            role="dialog"
            aria-labelledby="help-dialog-title">
            <div className="modal-dialog modal-dialog-centered"
                role="document">
                <div className="modal-content">
                    <div className="modal-header">
                        <h4 className="modal-title" id="confirmation-dialog-title">Help</h4>
                    </div>
                    <div className="modal-body help">
                        <p>The status panel shows you options to manage the <a href={url} target="_blank" rel="noopener noreferrer">MATLAB Integration for Jupyter</a>.</p>
                        <p>Use the buttons in the status panel to:</p>
                        <div>
                            <p className="icon-custom-start">Start your MATLAB session. Available if MATLAB is stopped.</p>
                            <p className="icon-custom-restart">Restart your MATLAB session. Available if MATLAB is running or starting.</p>
                            <p className="icon-custom-stop">Stop your MATLAB session. Use this option if you want to free up RAM and CPU resources. Available if MATLAB is running or starting.</p>
                            <p className="icon-custom-sign-out">
                                Sign out of MATLAB. Use this to stop MATLAB and to sign in with an alternative account. Available if using online licensing.<br/>
                                Unset network license manager server address. Use this to stop MATLAB and enter new licensing information. Available if using network license manager.
                            </p>
                            <p className="icon-custom-feedback">Send feedback about the MATLAB Integration for Jupyter. This action opens your default email application.</p>
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button onClick={closeHandler} data-testid='backBtn' className="btn btn_color_blue">Back</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

Help.propTypes = {
    closeHandler: PropTypes.func.isRequired
};

export default Help;
