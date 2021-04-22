// Copyright 2020-2021 The MathWorks, Inc.

import { createSelector } from 'reselect';

export const selectTutorialHidden = state => state.tutorialHidden;
export const selectServerStatus = state => state.serverStatus;
export const selectMatlabStatus = state => state.serverStatus.matlabStatus;
export const selectMatlabVersion = state => state.serverStatus.matlabVersion;
export const selectWsEnv = state => state.serverStatus.wsEnv;
export const selectSubmittingServerStatus = state => state.serverStatus.isSubmitting;
export const selectHasFetchedServerStatus = state => state.serverStatus.hasFetched;
export const selectLicensingInfo = state => state.serverStatus.licensingInfo;
export const selectLoadUrl = state => state.loadUrl;
export const selectServerStatusFetchFailCount = state => state.serverStatus.fetchFailCount;
export const selectError = state => state.error;

export const selectTriggerPosition = createSelector(
    state => state.triggerPosition,
    pos => pos === null ? undefined : pos
);

export const selectIsError = createSelector(
    selectError,
    error => error !== null
);

export const selectIsConnectionError = createSelector(
    selectServerStatusFetchFailCount,
    fails => fails >= 5
);

export const selectMatlabUp = createSelector(
    selectMatlabStatus,
    matlabStatus => matlabStatus === 'up'
);

export const selectMatlabRunning = createSelector(
    selectMatlabStatus,
    matlabStatus => matlabStatus === 'up' || matlabStatus === 'starting'
);

export const selectOverlayHidable = createSelector(
    selectMatlabStatus,
    selectIsError,
    (matlabStatus, isError) => (matlabStatus === 'up' && !isError)
);

export const selectOverlayVisibility = createSelector(
    state => state.overlayVisibility,
    selectMatlabUp,
    selectIsError,
    (visibility, matlabUp, isError) => (
        !matlabUp || visibility || isError
    )
);

export const getFetchAbortController = createSelector(
    selectServerStatus,
    serverStatus => serverStatus.fetchAbortController
);

export const selectFetchStatusPeriod = createSelector(
    selectMatlabStatus,
    selectSubmittingServerStatus,
    (matlabStatus, isSubmitting) => {
        if (isSubmitting) {
            return null;
        } else if (matlabStatus === 'up') {
            return 10000;
        }
        return 5000;
    }
);

export const selectLicensingProvided = createSelector(
    selectLicensingInfo,
    licensingInfo => Object.prototype.hasOwnProperty.call(licensingInfo, 'type')
);

export const selectLicensingIsMhlm = createSelector(
    selectLicensingInfo,
    selectLicensingProvided,
    (licensingInfo, licensingProvided) => licensingProvided && licensingInfo.type === 'MHLM'
);

export const selectLicensingMhlmUsername = createSelector(
    selectLicensingInfo,
    selectLicensingIsMhlm,
    (licensingInfo, isMhlm) => isMhlm ? licensingInfo.emailAddress : ''
);

// TODO Are these overkill? Perhaps just selecting status would be enough
// TODO Could be used for detected intermedia failures, such as server being
// temporarily inaccessible
export const selectMatlabPending = createSelector(
    selectMatlabStatus,
    matlabStatus => matlabStatus === 'starting'
);

export const selectOverlayVisible = createSelector(
    selectOverlayVisibility,
    selectIsError,
    (visibility, isError) => (visibility || isError)
);

export const selectInformationDetails = createSelector(
    selectMatlabStatus,
    selectIsError,
    (status, isError) => {

        switch (status) {
            case 'up':
                return {
                    label: 'Running',
                    icon: 'success',
                    alert: 'success'
                };
            case 'starting':
                return {
                    label: 'Starting. This may take several minutes.',
                    icon: 'info-reverse',
                    alert: 'info',
                    spinner: true
                };
            case 'down':
                const detail = {
                    label: 'Not running',
                    icon: 'info-reverse',
                    alert: 'info'
                };
                if (isError) {
                    detail.icon = 'error';
                    detail.alert = 'danger';
                }
                return detail;
            default:
                throw new Error(`Unknown MATLAB status: "${status}".`);
        }

    }
);
