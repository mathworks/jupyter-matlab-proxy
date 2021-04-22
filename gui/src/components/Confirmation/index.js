// Copyright 2020-2021 The MathWorks, Inc.

import React from 'react';
import PropTypes from 'prop-types';

function Confirmation({ confirm, cancel, children }) {
    return (
        <div className="modal show"
            id="confirmation"
            tabIndex="-1"
            role="dialog"
            aria-labelledby="confirmation-dialog-title">
            <div className="modal-dialog modal-dialog-centered"
                role="document">
                <div className="modal-content">
                    <div className="modal-header">
                        <h4 className="modal-title" id="confirmation-dialog-title">Confirmation</h4>
                    </div>
                    <div className="modal-body">
                        {children}
                    </div>
                    <div className="modal-footer">
                        <button onClick={cancel}  data-testid='cancelButton' className="btn companion_btn btn_color_blue">Cancel</button>
                        <button onClick={confirm} data-testid='confirmButton' className="btn btn_color_blue">Confirm</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

Confirmation.propTypes = {
    confirm: PropTypes.func.isRequired,
    cancel: PropTypes.func.isRequired,
    children: PropTypes.node.isRequired
};

export default Confirmation;
