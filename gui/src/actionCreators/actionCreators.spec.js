// Copyright 2020-2021 The MathWorks, Inc.

import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';
import fetchMock from 'fetch-mock';
import * as actions from '../actions';
import * as actionCreators from './index';

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);



describe.each([
  [actionCreators.setTutorialHidden, [true], {type:actions.SET_TUTORIAL_HIDDEN, hidden:true}],
  [actionCreators.setTutorialHidden, [false],  {type:actions.SET_TUTORIAL_HIDDEN, hidden:false}],
  [actionCreators.setOverlayVisibility, [true],  {type:actions.SET_OVERLAY_VISIBILITY, visibility:true}],
  [actionCreators.setOverlayVisibility, [false],  {type:actions.SET_OVERLAY_VISIBILITY, visibility:false}],
  [actionCreators.setTriggerPosition, [12,12],  {type:actions.SET_TRIGGER_POSITION, x:12, y:12}],
  [actionCreators.setTriggerPosition, [52,112],  {type:actions.SET_TRIGGER_POSITION, x:52, y:112}],
  ])('Test Set actionCreators', (method, input, expectedAction) => {
    test(`check if an action of type  ${expectedAction.type} is returned when method actionCreator.${method.name}() is called`, () => {
        expect(method(...input)).toEqual(expectedAction);
    });
  });


  describe.each([
  [actionCreators.requestServerStatus, {type:actions.REQUEST_SERVER_STATUS, fetchAbortController:new AbortController()}],
  [actionCreators.requestSetLicensing, {type:actions.REQUEST_SET_LICENSING, fetchAbortController:new AbortController()}],
  [actionCreators.requestStopMatlab, {type:actions.REQUEST_STOP_MATLAB, fetchAbortController:new AbortController()}],
  [actionCreators.requestStartMatlab, {type:actions.REQUEST_START_MATLAB, fetchAbortController:new AbortController()}],
  [actionCreators.requestTerminateIntegration, {type:actions.REQUEST_TERMINATE_INTEGRATION, fetchAbortController:new AbortController()}],
  ])('Test Request actionCreators', (method, expectedAction) => {

    let abortController;
    beforeAll(() => {
      abortController = new AbortController();
    });

    test(`check if an action of type  ${expectedAction.type} is returned with an AbortController when method actionCreator.${method.name}() is called`, () => {
        expect(method(abortController)).toEqual(expectedAction);

    });
  });


  describe.each([
  [actionCreators.receiveSetLicensing, {type: 'MHLM'}, {type:actions.RECEIVE_SET_LICENSING, status:{type:'MHLM'}}],
  [actionCreators.receiveStopMatlab,{matlabStatus:'down'}, {type:actions.RECEIVE_STOP_MATLAB, status:{matlabStatus:'down'}}],
  [actionCreators.receiveStartMatlab,{matlabStatus:'up'}, {type:actions.RECEIVE_START_MATLAB, status:{matlabStatus:'up'}}],
  [actionCreators.receiveError, {message:'ERROR: License Manager Error -9', logs: null}, {type:actions.RECEIVE_ERROR, error: {message:'ERROR: License Manager Error -9', logs: null}}],
  [actionCreators.receiveTerminateIntegration,{licensing:{}}, {type:actions.RECEIVE_TERMINATE_INTEGRATION, status:{licensing:{}}, loadUrl:'../'}],
  ])('Test Receive actionCreators', (method, input, expectedAction) => {

    test(`check if an action of type  ${expectedAction.type} is returned when method actionCreator.${method.name}() is called`, () => {
        expect(method(input)).toEqual(expectedAction);

    });
  });



describe('Test sync actionCreators using redux-thunk', () => {
  it('should dispatch action of type RECEIVE_SERVER_STATUS ', () => {
    const store = mockStore({
      overlayVisibility: false,
      error: null,
      serverStatus: {
        matlabStatus: 'starting',
        matlabVersion: 'R2020b',
        isFetching: true,
        hasFetched: false,
        fetchFailCount: 0,
        licensingInfo: {
          type: 'NLM',
          connectionString: 'abc@nlm',
        },
        fetchAbortController: new AbortController(),
      },
    });

    const status = {
      matlab: {
        status: 'up',
      },
      licensing: {
        type: 'MHLM',
      },
    };
    store.dispatch(actionCreators.receiveServerStatus(status));

    const expectedActionTypes = [actions.RECEIVE_SERVER_STATUS];

    const receivedActions = store.getActions();

    expect(receivedActions.map((element) => element.type)).toEqual(
      expectedActionTypes
    );
  });
});

describe('async actionCreators', () => {
  let store;
  beforeEach(() => {
    store = mockStore({
      error: null,
      serverStatus: {
        matlabVersion: 'R2020b',
        licensingInfo: {
          type: 'NLM',
          connectionString: 'abc@nlm',
        },
        isFetching: false,
        isSubmitting: false,
        hasFetched: false,
        fetchFailCount: 0,
        fetchAbortController: new AbortController(),
      },
    });
  });

  afterEach(() => {
    fetchMock.restore();
  });

  it('dispatches REQUEST_SERVER_STATUS and RECEIVE_SERVER_STATUS when fetching status', () => {
    fetchMock.getOnce('/get_status', {
      body: {
        matlab: {
          status: 'down',
        },
        licensing: {},
      },
      headers: { 'content-type': 'application/json' },
    });

    const expectedActions = [
      actions.REQUEST_SERVER_STATUS,
      actions.RECEIVE_SERVER_STATUS,
    ];

    return store.dispatch(actionCreators.fetchServerStatus()).then(() => {
      const received = store.getActions();
      expect(received.map((a) => a.type)).toEqual(expectedActions);
    });
  });

  it('should dispatch REQUEST_SET_LICENSING and RECEIVE_SET_LICENSING when we set license', () => {
    fetchMock.putOnce('/set_licensing_info', {
      body: {
        matlab: {
          status: 'up',
        },
        licensing: {
          type: 'NLM',
          connectionString: 'abc@nlm',
        },
      },
      headers: { 'content-type': 'application/json' },
    });

    const expectedActionTypes = [
      actions.REQUEST_SET_LICENSING,
      actions.RECEIVE_SET_LICENSING,
    ];
    const info = {
      type: 'NLM',
      connectionString: 'abc@nlm',
    };
    return store.dispatch(actionCreators.fetchSetLicensing(info)).then(() => {
      const receivedActions = store.getActions();
      expect(receivedActions.map((action) => action.type)).toEqual(
        expectedActionTypes
      );
    });
  });

  it('should dispatch REQUEST_SET_LICENSING and RECEIVE_SET_LICENSING when we unset license', () => {
    fetchMock.deleteOnce('./set_licensing_info', {
      body: {
        matlab: {
          status: 'down',
        },
        licensing: null,
      },
      headers: { 'content-type': 'application/json' },
    });

    const expectedActionTypes = [
      actions.REQUEST_SET_LICENSING,
      actions.RECEIVE_SET_LICENSING,
    ];

    return store.dispatch(actionCreators.fetchUnsetLicensing()).then(() => {
      const receivedActions = store.getActions();
      expect(receivedActions.map((action) => action.type)).toEqual(
        expectedActionTypes
      );
    });
  });

  it('should dispatch REQUEST_TERMINATE_INTEGRATION and RECEIVE_TERMINATE_INTEGRATION when we terminate the integration', () => {
    fetchMock.deleteOnce('./terminate_integration', {
      body: {
        matlab: {
          status: 'down',
        },
        licensing: null,
      },
      headers: { 'content-type': 'application/json' },
    });

    const expectedActionTypes = [
      actions.REQUEST_TERMINATE_INTEGRATION,
      actions.RECEIVE_TERMINATE_INTEGRATION,
    ];

    return store
      .dispatch(actionCreators.fetchTerminateIntegration())
      .then(() => {
        const receivedActions = store.getActions();
        expect(receivedActions.map((action) => action.type)).toEqual(
          expectedActionTypes
        );
      });
  });

  it('should dispatch REQUEST_STOP_MATLAB AND RECEIVE_STOP_MATLAB when we stop matlab', () => {
    fetchMock.deleteOnce('./stop_matlab', {
      body: {
        matlab: {
          status: 'down',
        },
        licensing: null,
      },
      headers: { 'content-type': 'application/json' },
    });

    const expectedActionTypes = [
      actions.REQUEST_STOP_MATLAB,
      actions.RECEIVE_STOP_MATLAB,
    ];

    return store.dispatch(actionCreators.fetchStopMatlab()).then(() => {
      const receivedActions = store.getActions();
      expect(receivedActions.map((action) => action.type)).toEqual(
        expectedActionTypes
      );
    });
  });

  it('should dispatch REQUEST_STOP_MATLAB AND RECEIVE_STOP_MATLAB when we stop matlab', () => {
    fetchMock.putOnce('./start_matlab', {
      body: {
        matlab: {
          status: 'down',
        },
        licensing: null,
      },
      headers: { 'content-type': 'application/json' },
    });

    const expectedActionTypes = [
      actions.REQUEST_START_MATLAB,
      actions.RECEIVE_START_MATLAB,
    ];

    return store.dispatch(actionCreators.fetchStartMatlab()).then(() => {
      const receivedActions = store.getActions();
      expect(receivedActions.map((action) => action.type)).toEqual(
        expectedActionTypes
      );
    });
  });
});
