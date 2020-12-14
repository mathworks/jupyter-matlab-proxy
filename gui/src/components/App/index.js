// Copyright 2020 The MathWorks, Inc.

import React, { useState, useCallback, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useInterval } from 'react-use';
import './App.css';
import Confirmation from '../Confirmation';
import OverlayTrigger from '../OverlayTrigger';
import Overlay from '../Overlay';
import MatlabJsd from '../MatlabJsd';
import LicensingGatherer from '../LicensingGatherer';
import Controls from '../Controls';
import Information from '../Information';
import Help from '../Help';
import Error from '../Error';
import {
    selectOverlayVisible,
    selectFetchStatusPeriod,
    selectHasFetchedServerStatus,
    selectLicensingProvided,
    selectMatlabUp,
    selectError,
    selectLoadUrl,
    selectIsConnectionError,
} from '../../selectors';
import {
    setOverlayVisibility,
    fetchServerStatus
} from '../../actionCreators';

function App() {
    const dispatch = useDispatch();

    const overlayVisible = useSelector(selectOverlayVisible);
    const fetchStatusPeriod = useSelector(selectFetchStatusPeriod);
    const hasFetchedServerStatus = useSelector(selectHasFetchedServerStatus);
    const licensingProvided = useSelector(selectLicensingProvided);
    const matlabUp = useSelector(selectMatlabUp);
    const error = useSelector(selectError);
    const loadUrl = useSelector(selectLoadUrl);
    const isConnectionError = useSelector(selectIsConnectionError);

    const toggleOverlayVisible = useCallback(
        () => dispatch(setOverlayVisibility(!overlayVisible)),
        [overlayVisible, dispatch]
    );

    const [dialogModel, setDialogModel] = useState(null);

    let dialog;
    if (dialogModel) {
        const closeHandler = () => setDialogModel(null);
        const dismissAllHandler = () => {
            closeHandler();
            toggleOverlayVisible(false);
        };
        switch (dialogModel.type) {
            case 'confirmation':
                const confirm = () => {
                    dispatch(dialogModel.callback());
                    setDialogModel(null);
                };
                dialog = (
                    <Confirmation
                        confirm={confirm}
                        cancel={closeHandler}>
                        {dialogModel.message || ''}
                    </Confirmation>
                );
                break;
            case 'help':
                dialog = (
                    <Help
                        closeHandler={closeHandler}
                        dismissAllHandler={dismissAllHandler}
                    />);
                break;
            default:
                throw new Error(`Unknown dialog type: ${dialogModel.type}.`);
        }
    }
    if (isConnectionError) {
        dialog = (
            <Error
                message="Either this integration terminated or the session ended"
            >
                <p>Attempt to <a href="../">return to a parent app</a></p>
            </Error>
        );
    } else if (error && error.type === "MatlabInstallError") {
        dialog = <Error message={error.message} />;
    }

    // Initial fetch server status
    useEffect(() => {
        if (!hasFetchedServerStatus) {
            dispatch(fetchServerStatus());
        }
    }, [dispatch, hasFetchedServerStatus]);

    // Periodic fetch server status
    useInterval(() => {
        dispatch(fetchServerStatus());
    }, fetchStatusPeriod);

    // Load URL
    useEffect(() => {
        if (loadUrl !== null) {
            window.location.href = loadUrl;
        }
    }, [loadUrl]);

    // Display one of:
    // * Confirmation
    // * Help
    // * Error
    // * License gatherer
    // * Status
    let overlayContent;
    if (dialog) {
        // TODO Inline confirmation component build
        overlayContent = dialog;
    } else if (hasFetchedServerStatus && (!licensingProvided)) {
        overlayContent = <LicensingGatherer />;
    } else if (licensingProvided && !dialog) {
        overlayContent = (
            <Information closeHandler={toggleOverlayVisible}>
                <Controls callback={args => setDialogModel(args)}/>
            </Information>
        );
    }

    const overlay = overlayVisible ? (
        <Overlay>
            {overlayContent}
        </Overlay>
    ) : null;

    // FIXME Until https://github.com/http-party/node-http-proxy/issues/1342
    // is addressed, use a direct URL in development mode. Once that is
    // fixed, the request will be served by the fake MATLAB Embedded Connector
    // process in development mode
    const matlabUrl = process.env.NODE_ENV === 'development'
        ? 'http://localhost:31515/index-jsd-cr.html'
        : './index-jsd-cr.html';

    const matlabJsd = matlabUp ? (
        <MatlabJsd url={matlabUrl} />
    ) : null;

    const overlayTrigger = overlayVisible ? null : <OverlayTrigger />;

    return (
        <div data-testid="app" className="main">
            {overlayTrigger}
            {matlabJsd}
            {overlay}
        </div>
    );
}

export default App;
