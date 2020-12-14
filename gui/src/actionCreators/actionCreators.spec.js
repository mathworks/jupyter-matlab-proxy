// Copyright 2020 The MathWorks, Inc.

import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import fetchMock from 'fetch-mock';
import * as actions from '../actions';
import * as actionCreators from './index';

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);

// Example of testing basic action creator
describe('actionCreators', () => {
    it('should create an action to set the overlay visible', () => {
        const expectedAction = {
            type: actions.SET_OVERLAY_VISIBILITY,
            visibility: true
        };
        expect(
            actionCreators.setOverlayVisibility(true)
        ).toEqual(expectedAction)
    });
});

// Example of testing async (thunk) action creator
describe('async actionCreators', () => {
    afterEach(() => {
        fetchMock.restore()
    });

    it('dispatches REQUEST_SERVER_STATUS and RECEIVE_SERVER_STATUS when fetching status', () => {
        fetchMock.getOnce('/get_status', {
            body: {
                matlab: {
                    status: 'down'
                },
                licensing: {}
            },
            headers: { 'content-type': 'application/json' }
        });

        const abortController = new AbortController();
        abortController.signal;

        const store = mockStore({
            serverStatus: {
                licensingInfo: {},
                matlabStatus: 'down',
                fetchAbortController: new AbortController()
            }
        });

        const expectedActions = [
            actions.REQUEST_SERVER_STATUS,
            actions.RECEIVE_SERVER_STATUS
        ];

        return store.dispatch(actionCreators.fetchServerStatus()).then(() => {
            const received = store.getActions();
            expect(
                received.map(a => a.type)
            ).toEqual(expectedActions);
        })
    })
})