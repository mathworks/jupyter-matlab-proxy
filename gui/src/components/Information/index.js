// Copyright 2020 The MathWorks, Inc.

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useSelector } from 'react-redux';
import Linkify from 'react-linkify';
import {
    selectLicensingInfo,
    selectError,
    selectOverlayHidable,
    selectInformationDetails
} from '../../selectors';
import './Information.css';

function Information({
    closeHandler,
    children
}) {
    const licensingInfo = useSelector(selectLicensingInfo);
    const error = useSelector(selectError);
    const overlayHidable = useSelector(selectOverlayHidable);

    const [errorLogsExpanded, setErrorLogsExpanded] = useState(false);
    const errorLogsExpandedToggle = () => {
        setErrorLogsExpanded(!errorLogsExpanded);
    };

    let info;
    switch (licensingInfo?.type) {
        case "MHLM":
            info = {
                label: `Online License Manager (${licensingInfo.emailAddress})`
            };
            break;
        case "NLM":
            info = {
                label: `Network License Manager (${licensingInfo.connectionString})`
            };
            break;
        default:
            info = {
                label: 'None'
            };
    }

    const details = useSelector(selectInformationDetails);

    const errorMessageNode = error ? (
        <div className="error-container alert alert-danger">
            <p><strong>Error</strong></p>
            <Linkify>
                <div className="error-text">{error.message}</div>
            </Linkify>
        </div>
    ) : null;

    const errorLogsNode = (error && error.logs !== null && error.logs.length > 0) ? (
        <div className="expand_collapse error-logs-container">
            <h4 className={`expand_trigger ${errorLogsExpanded ? 'expanded' : 'collapsed'}`}
                onClick={errorLogsExpandedToggle}>
                <span className="icon-arrow-open-down"></span>
                <span className="icon-arrow-open-right"></span>
                Error logs
            </h4>
            <div id="error-logs"
                className={`expand_target error-container alert alert-danger ${errorLogsExpanded ? 'expanded' : 'collapsed'}`}
                aria-expanded={errorLogsExpanded}>
                <Linkify>
                    <div className="error-msg">{error.logs.join('\n').trim()}</div>
                </Linkify>
            </div>
        </div>
    ) : null;

    const onCloseClick = event => {
        if(event.target === event.currentTarget) {
            event.preventDefault();
            closeHandler();
        }
    };

    return (
        <div className="modal show"
            id="information"
            onClick={overlayHidable ? onCloseClick : null}
            tabIndex="-1"
            role="dialog"
            aria-labelledby="information-dialog-title">
            <div className="modal-dialog modal-dialog-centered" role="document">
                <div className={`modal-content alert alert-${details.alert}`}>
                    <div className="modal-header">
                        {
                            overlayHidable && (
                                <button
                                    type="button"
                                    className="close"
                                    data-dismiss="modal"
                                    aria-label="Close"
                                    onClick={closeHandler}>
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            )
                        }
                        <span className={`alert_icon icon-alert-${details.icon}`}/>
                        <h4 className="modal-title alert_heading" id="information-dialog-title">Status Information</h4>
                    </div >
                    <div className="modal-body">
                        <table className="details">
                            <tbody>
                                <tr>
                                    <td>MATLAB Status:</td>
                                    <td>
                                        <span id="spinner"
                                            className={details.spinner ? 'show' : 'hidden'}
                                        ></span>
                                        {details.label}
                                    </td>
                                </tr>
                                <tr>
                                    <td>Licensing:</td>
                                    <td>{info.label}</td>
                                </tr>
                            </tbody>
                        </table>
                        {errorMessageNode}
                        {errorLogsNode}
                    </div>
                    <div className="modal-footer">
                        {children}
                    </div>
                </div>
            </div>
        </div>
    );
}

Information.propTypes = {
    closeHandler: PropTypes.func.isRequired
};

export default Information;
