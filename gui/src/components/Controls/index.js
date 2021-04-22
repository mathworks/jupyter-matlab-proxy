// Copyright 2020-2021 The MathWorks, Inc.

import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import { useSelector } from 'react-redux';
import ReactTooltip from 'react-tooltip';
import {
    selectSubmittingServerStatus,
    selectLicensingIsMhlm,
    selectLicensingProvided,
    selectMatlabRunning,
    selectMatlabVersion,
    selectError
} from '../../selectors';
import {
    fetchStartMatlab,
    fetchStopMatlab,
    fetchTerminateIntegration,
    fetchUnsetLicensing
} from '../../actionCreators';
import './Controls.css';

// Suggested actions for certain errors
const ERROR_TYPE_MAP = {
    'sign-out': ['NetworkLicensingError', 'EntitlementError'],
    'restart': ['OnlineLicensingError']
};

function Controls({
    callback
}) {
    const submitting = useSelector(selectSubmittingServerStatus);
    const licensed = useSelector(selectLicensingProvided);
    const mhlmLicense = useSelector(selectLicensingIsMhlm);
    const matlabRunning = useSelector(selectMatlabRunning);
    const matlabVersion = useSelector(selectMatlabVersion);
    const error = useSelector(selectError);

//     const canTerminateIntegration = !submitting;
    const canResetLicensing = licensed && !submitting;

    const feedbackBody = useMemo(
        () => `%0D%0A
Thank you for providing feedback.%0D%0A
%0D%0A
MATLAB version: ${matlabVersion}%0D%0A`,
        [matlabVersion]
    );

    const Confirmations = {
        START: {
            type: 'confirmation',
            message: `Are you sure you want to ${matlabRunning ? 're' : ''}start MATLAB?`,
            callback: fetchStartMatlab
        },
        STOP: {
            type: 'confirmation',
            message: 'Are you sure you want to stop MATLAB?',
            callback: fetchStopMatlab
        },
        TERMINATE: {
            type: 'confirmation',
            message: 'Are you sure you want to terminate MATLAB and this Jupyter integration?',
            callback: fetchTerminateIntegration
        },
        SIGN_OUT: {
            type: 'confirmation',
            message: `Are you sure you want to ${mhlmLicense ? 'sign out of MATLAB' : 'unset the connection string'}?`,
            callback: fetchUnsetLicensing
        },
        HELP: {
            type: 'help'
        }
    };

    function getBtnClass (btn) {
        let cls = 'btn companion_btn ';
        if (error) {
            if ((ERROR_TYPE_MAP[btn] || []).includes(error.type)) {
                return cls + 'btn_color_blue';
            }
        } else if (btn === 'start') {
            // if there's no error, then highlight the "Start" button (if visible)
            return cls + 'btn_color_blue';
        }
        return cls + 'btn_color_mediumgray';
    };

    return (
        <div id="controls" className="labels-on-top">
            <button
                id="startMatlab"
                data-testid='startMatlabBtn'
                className={getBtnClass(matlabRunning ? 'restart' : 'start')}
                onClick={() => callback(Confirmations.START)}
                disabled={!licensed}
                data-for="control-button-tooltip"
                data-tip={`${matlabRunning ? 'Restart' : 'Start'}  your MATLAB session`}
            >
                <span className={`icon-custom-${matlabRunning ? 're' : ''}start`}></span>
                <span className='btn-label'>{`${matlabRunning ? 'Restart' : 'Start'} MATLAB Session`}</span>
            </button>
            <button
                id="stopMatlab"
                data-testid='stopMatlabBtn'
                className={getBtnClass('stop')}
                onClick={() => callback(Confirmations.STOP)}
                disabled={!matlabRunning}
                data-for="control-button-tooltip"
                data-tip="Stop your MATLAB session"
            >
                <span className='icon-custom-stop'></span>
                <span className='btn-label'>Stop MATLAB Session</span>
            </button>
            <button
                id="unsetLicensing"
                data-testid='unsetLicensingBtn'
                className={getBtnClass('sign-out')}
                onClick={() => callback(Confirmations.SIGN_OUT)}
                disabled={!canResetLicensing}
                data-for="control-button-tooltip"
                data-tip={mhlmLicense ? 'Sign out' : 'Unset the network license manager server address'}
            >
                <span className='icon-custom-sign-out'></span>
                <span className='btn-label'>{mhlmLicense ? 'Sign Out' : 'Unset License Server Address'}</span>
            </button>
            {/* <button
                id="terminateIntegration"
                className="btn btn_color_mediumgray companion_btn"
                style={{display: 'none'}}
                onClick={() => callback(Confirmations.TERMINATE)}
                disabled={!canTerminateIntegration}
                data-for="control-button-tooltip"
                data-tip="Terminate your MATLAB and MATLAB in Jupyter sessions"
            >
                <span className='icon-custom-terminate'></span>
                <span className='btn-label'>End Session</span>
            </button> */}
            <a
                id="feedback"
                data-testid='feedbackLink'
                className="btn btn_color_mediumgray companion_btn"
                href={ `mailto:jupyter-support@mathworks.com?subject=MATLAB Integration for Jupyter Feedback&body=${feedbackBody}` }
                data-for="control-button-tooltip"
                data-tip="Send feedback (opens your default email application)"
            >
                <span className='icon-custom-feedback'></span>
                <span className='btn-label'>Feedback</span>
            </a>
            <button
                id="Help"
                data-testid='helpBtn'
                className="btn btn_color_mediumgray companion_btn"
                onClick={() => callback(Confirmations.HELP)}
                data-for="control-button-tooltip"
                data-tip="See a description of the buttons"
            >
                <span className='icon-custom-help'></span>
                <span className='btn-label'>Help</span>
            </button>
            <ReactTooltip
                id="control-button-tooltip"
                place="top"
                type="info"
                effect="solid"
            />
        </div>
    );
}

Controls.propTypes = {
    confirmHandler: PropTypes.func
};

export default Controls;
