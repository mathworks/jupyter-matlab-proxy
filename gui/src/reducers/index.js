// Copyright 2020-2021 The MathWorks, Inc.

import { combineReducers } from 'redux';

// ACTIONS
import {
    SET_TRIGGER_POSITION,
    SET_TUTORIAL_HIDDEN,
    SET_OVERLAY_VISIBILITY,
    REQUEST_SERVER_STATUS,
    RECEIVE_SERVER_STATUS,
    REQUEST_SET_LICENSING,
    REQUEST_TERMINATE_INTEGRATION,
    REQUEST_STOP_MATLAB,
    REQUEST_START_MATLAB,
    RECEIVE_SET_LICENSING,
    RECEIVE_TERMINATE_INTEGRATION,
    RECEIVE_STOP_MATLAB,
    RECEIVE_START_MATLAB,
    RECEIVE_ERROR
} from '../actions';

export function triggerPosition(state={x: window.innerWidth / 2 + 27, y: 0}, action) {
    switch (action.type) {
        case SET_TRIGGER_POSITION:
            return {x: action.x, y: action.y};
        default:
            return state;
    }
}

export function tutorialHidden(state=false, action) {
    switch (action.type) {
        case SET_TUTORIAL_HIDDEN:
            return action.hidden;
        default:
            return state;
    }
}

export function overlayVisibility(state = false, action) {
    switch (action.type) {
        case SET_OVERLAY_VISIBILITY:
            return action.visibility;
        case RECEIVE_SERVER_STATUS:
            if (
                action.previousMatlabPending === true
                && action.status.matlab.status === "up"
            ) return false;
            // fall through
        default:
            return state;
    }
}

export function licensingInfo(state = {}, action) {
    switch (action.type) {
        case RECEIVE_SERVER_STATUS:
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
            return {
                ...action.status.licensing
            };
        default:
            return state;
    }
}

export function matlabStatus(state = 'down', action) {
    switch (action.type) {
        case RECEIVE_SERVER_STATUS:
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
            return action.status.matlab.status;
        default:
            return state;
    }
}

export function matlabVersion(state=null, action) {
    switch (action.type) {
        case RECEIVE_SERVER_STATUS:
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
            return action.status.matlab.version;
        default:
            return state;
    }
}

export function wsEnv(state=null, action) {
    switch (action.type) {
        case RECEIVE_SERVER_STATUS:
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
            return action.status.wsEnv;
        default:
            return state;
    }
}

export function isFetching(state = false, action) {
    switch (action.type) {
        case REQUEST_SERVER_STATUS:
        case REQUEST_SET_LICENSING:
        case REQUEST_TERMINATE_INTEGRATION:
        case REQUEST_STOP_MATLAB:
        case REQUEST_START_MATLAB:
            return true;
        case RECEIVE_SERVER_STATUS:
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
        case RECEIVE_ERROR:
            return false;
        default:
            return state;
    }
}

export function hasFetched(state = false, action) {
    switch (action.type) {
        case RECEIVE_SERVER_STATUS:
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
            return true;
        default:
            return state;
    }
}

export function isSubmitting(state = false, action) {
    switch (action.type) {
        case REQUEST_SET_LICENSING:
        case REQUEST_TERMINATE_INTEGRATION:
        case REQUEST_STOP_MATLAB:
        case REQUEST_START_MATLAB:
            return true;
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
        case RECEIVE_ERROR:
            return false;
        default:
            return state;
    }
}

export function fetchAbortController(state = new AbortController(), action) {
    switch (action.type) {
        case REQUEST_SERVER_STATUS:
        case REQUEST_SET_LICENSING:
        case REQUEST_TERMINATE_INTEGRATION:
        case REQUEST_STOP_MATLAB:
        case REQUEST_START_MATLAB:
            return action.fetchAbortController;
        default:
            return state;
    }
}

export function fetchFailCount(state = 0, action) {
    switch (action.type) {
        case RECEIVE_SERVER_STATUS:
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
            return 0;
        case RECEIVE_ERROR:
            return state + 1;
        default:
            return state;

    }
}

export function loadUrl(state = null, action) {
    switch (action.type) {
        case RECEIVE_TERMINATE_INTEGRATION:
            return action.loadUrl;
        default:
            return state;
    }
}

export function error(state = null, action) {
    switch (action.type) {
        case RECEIVE_ERROR:
            return {
                message: action.error,
                logs: null
            };
        case RECEIVE_SERVER_STATUS:
        case RECEIVE_SET_LICENSING:
        case RECEIVE_TERMINATE_INTEGRATION:
        case RECEIVE_STOP_MATLAB:
        case RECEIVE_START_MATLAB:
            return action.status.error ? {
                message: action.status.error.message,
                logs: action.status.error.logs,
                type: action.status.error.type
            } : null;
        default:
            return state;
    }
}

export const serverStatus = combineReducers({
    licensingInfo,
    matlabStatus,
    matlabVersion,
    wsEnv,
    isFetching,
    hasFetched,
    isSubmitting,
    fetchAbortController,
    fetchFailCount
});

export default combineReducers({
    triggerPosition,
    tutorialHidden,
    overlayVisibility,
    serverStatus,
    loadUrl,
    error
});