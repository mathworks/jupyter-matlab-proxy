// Copyright 2020-2021 The MathWorks, Inc.

import * as reducers from './index';
import * as actions from '../actions';
import { receiveTerminateIntegration } from '../actionCreators';

const _ = require('lodash');

describe('reducers', () => {
  let genericAction, action;
  let receiveActions = [],
    requestActions = [];

  beforeAll(() => {
    genericAction = {
      type: '',
      error: 'Licensing Error',
      fetchAbortController: new AbortController(),
      loadUrl: '/',
      hidden: true,
      x: 12,
      y: 12,
      previousMatlabPending: true,
      status: {
        wsEnv: 'mw-integ',
        matlab: {
          status: 'up',
          version: 'R2020b',
        },
        licensing: {
          type: 'MHLM',
        },
      },
    };

    receiveActions.push(
      actions.RECEIVE_SERVER_STATUS,
      actions.RECEIVE_SET_LICENSING,
      actions.RECEIVE_TERMINATE_INTEGRATION,
      actions.RECEIVE_STOP_MATLAB,
      actions.RECEIVE_START_MATLAB
    );

    requestActions.push(
      actions.REQUEST_SERVER_STATUS,
      actions.REQUEST_SET_LICENSING,
      actions.REQUEST_TERMINATE_INTEGRATION,
      actions.REQUEST_STOP_MATLAB,
      actions.REQUEST_START_MATLAB
    );
  });

  describe('overlayVisibility', () => {
    it('should return the intial state', () => {
      expect(reducers.overlayVisibility(undefined, genericAction)).toEqual(false);
    });

    it('should handle SET_OVERLAY_VISIBILITY', () => {
      // Set visibility to true
      action = _.cloneDeep(genericAction);
      action.type = actions.SET_OVERLAY_VISIBILITY;
      action.visibility = true;
      expect(reducers.overlayVisibility(undefined, action)).toBe(true);

      // set visibility to false
      action = _.cloneDeep(genericAction);
      action.type = actions.SET_OVERLAY_VISIBILITY;
      action.visibility = false;
      expect(reducers.overlayVisibility(undefined, action)).toBe(false);
    });

    it('should handle RECEIVE_SERVER_STATUS', () => {

      action = _.cloneDeep(genericAction);
      action.type = actions.RECEIVE_SERVER_STATUS;

      // If matlab status is up, visibility should be false
      expect(reducers.overlayVisibility(undefined, action)).toBe(false);

      //If previousMatlabPending is false, visibility should be false

      action = _.cloneDeep(genericAction);
      action.previousMatlabPending = false;
      expect(reducers.overlayVisibility(undefined, action)).toBe(false);

      // If matlab status is down, should return default state
      action = _.cloneDeep(genericAction);
      action.previousMatlabPending = true;
      action.status.matlab.status = 'down';
      expect(reducers.overlayVisibility(undefined, action)).toBe(false);
    });

    it('should return current state when unknown action.type', () => {

      action = _.cloneDeep(genericAction);
      action.type = actions.RECEIVE_SET_LICENSING;

      expect(reducers.overlayVisibility(undefined, action)).toBe(false);
      expect(reducers.overlayVisibility(true, action)).toBe(true);
    });
  });

  describe('triggerPosition', () => {
    it('should return trigger x,y positions', () => {

      action = _.cloneDeep(genericAction);
      action.type = actions.SET_TRIGGER_POSITION;

      // expect to return the same trigger x,y positions
      expect(reducers.triggerPosition(undefined, action)).toMatchObject({
        x: action.x,
        y: action.y,
      });

      // check default case
      action = _.cloneDeep(genericAction);
      expect(reducers.triggerPosition(undefined, action)).not.toBeUndefined();
    });
  });

  describe('tutorialHidden', () => {
    it('should set tutorialHidden', () => {

      action = _.cloneDeep(genericAction);
      action.type = actions.SET_TUTORIAL_HIDDEN;

      // Expect tutorialHidden to be true
      expect(reducers.tutorialHidden(undefined, action)).toBe(true);

      // Expect tutorialHidden to be false
      action = _.cloneDeep(genericAction);
      action.type = action.SET_TUTORIAL_HIDDEN;
      action.hidden = false;
      expect(reducers.tutorialHidden(undefined, action)).toBe(false);

      // Check default case
      action = _.cloneDeep(genericAction);
      expect(reducers.tutorialHidden(true, action)).toBe(true);
      expect(reducers.tutorialHidden(false, action)).toBe(false);
    });
  });

  describe('licensingInfo', () => {

    it('should return licensing info for actions defined in receiveActions array', () => {
      for (let i = 0; i < receiveActions.length; i++) {
        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];
        expect(reducers.licensingInfo(undefined, action)).toMatchObject(
          action.status.licensing
        );
      }
    });

    it('should return empty object as default state', () => {
      action = _.cloneDeep(genericAction);
      const state = reducers.licensingInfo(undefined, action);
      expect(typeof state).toBe('object');
    });
  });

  describe('matlabStatus', () => {

    it('should return matlab status for actions defined in receiveActions', () => {
      for (let i = 0; i < receiveActions.length; i++) {

        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];

        expect(reducers.matlabStatus(undefined, action)).toEqual(
          action.status.matlab.status
        );
      }
    });

    it('should return matlab status down as default', () => {
       action = _.cloneDeep(genericAction);
      expect(reducers.matlabStatus(undefined, action)).toEqual('down');
    });
  });

  describe('matlabVersion', () => {


    it('should return matlab version for action type defined in receiveActions', () => {
      for (let i = 0; i < receiveActions.length; i++) {
        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];
        expect(reducers.matlabVersion(undefined, action)).toBe(
          action.status.matlab.version
        );
      }
    });

    it('should return matlab version : null as default', () => {
      action = _.cloneDeep(genericAction);
      expect(reducers.matlabVersion(undefined, action)).toBeNull();
    });
  });

  describe('wsEnv', () => {

    it('should return wsEnv value for action type defined in receiveActions', () => {
      for (let i = 0; i < receiveActions.length; i++) {
        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];
        expect(reducers.wsEnv(undefined, action)).toBe(
          action.status.wsEnv
        );
      }
    });

    it('should return null by default', () => {
      action = _.cloneDeep(genericAction);
      action.type = actions.REQUEST_SERVER_STATUS;
      expect(reducers.wsEnv(undefined, action)).toBeNull();
    });
  });



  describe('isFetching', () => {

    it('should return True for actions in requestActions and False for receiveActions', () => {
      for (let i = 0; i < requestActions.length; i++) {
        action = _.cloneDeep(genericAction);
        action.type = requestActions[i];
        expect(reducers.isFetching(undefined, action)).toBe(true);


        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];
        expect(reducers.isFetching(undefined, action)).toBe(false);
      }
    });

    it('should return false for RECEIVE_ERROR', () => {
      action = _.cloneDeep(genericAction);
      action.type = actions.RECEIVE_ERROR;
      expect(reducers.isFetching(undefined, action)).toBe(false);
    });

    it('Check default case', () => {
      action = _.cloneDeep(genericAction);
      expect(reducers.isFetching(false, action)).toBe(false);
      expect(reducers.isFetching(true, action)).toBe(true);
    });
  });

  describe('hasFetched', () => {

    it('should return true for actions defined in receiveActions', () => {
      for (let i = 0; i < receiveActions.length; i++) {
        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];
        expect(reducers.hasFetched(undefined, action)).toBe(true);
      }
    });

    it('Check default case', () => {
      action = _.cloneDeep(genericAction);
      expect(reducers.hasFetched(undefined, action)).toBe(false);
      expect(reducers.hasFetched(true, action)).toBe(true);
    });
  });

  describe('isSubmitting', () => {


    it('should return true for action types in requestActions except REQUEST_SERVER_STATUS and false for action types in receiveActions', () => {
      for (let i = 0; i < requestActions.length; i++) {

        action = _.cloneDeep(genericAction);
        action.type = requestActions[i];

        // expect to be true for request action type
        if (action.type !== actions.REQUEST_SERVER_STATUS) {
          expect(reducers.isSubmitting(undefined, action)).toBe(true);
        }

        // expect to be false for receive action type
        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];
        expect(reducers.isSubmitting(undefined, action)).toBe(false);
      }
    });

    it('Check default case', () => {
      action = _.cloneDeep(genericAction);
      expect(reducers.isSubmitting(undefined, action)).toBe(false);
      expect(reducers.isSubmitting(true, action)).toBe(true);
    });
  });

  describe('fetchAbortController', () => {

    it('should return a AbortController object defined within the action object', () => {
      for (let i = 0; i < requestActions.length; i++) {
        action = _.cloneDeep(genericAction);
        action.type = requestActions[i];
        expect(reducers.fetchAbortController(undefined, action)).toStrictEqual(
          action.fetchAbortController
        );
      }
    });

    // Check default state
    it('should return new AbortController object in default case', () => {
      action = _.cloneDeep(genericAction);
      const abortController = new AbortController();
      expect(reducers.fetchAbortController(abortController, action)).toEqual(abortController);
    });
  });

  describe('fetchFailCount', () => {

    it('should maintain state value at 0 for action types in receiveActions', () => {
      for (let i = 0; i < receiveActions.length; i++) {
        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];
        expect(reducers.fetchFailCount(0, action)).toEqual(0);
      }
    });

    // For action type : RECEIVE_ERROR increment failcount.
    it('should increment state value when action type : RECEIVE_ERROR', () => {
      action = _.cloneDeep(genericAction);
      action.type = actions.RECEIVE_ERROR;
      let state = 0;
      expect(reducers.fetchFailCount(state, action)).toEqual(state + 1);
      state = 3;
      expect(reducers.fetchFailCount(state, action)).toEqual(state + 1);
    });

    it('should maintain the same state value in default case', () => {
      action = _.cloneDeep(genericAction);
      expect(reducers.fetchFailCount(1, action)).toEqual(1);
    });
  });

  describe('loadUrl', () => {

    it('should by default return null', () => {
      action = _.cloneDeep(genericAction);
      expect(reducers.loadUrl(undefined, action)).toBeNull();
    });

    it('should return loadUrl when action is RECEIVE_TERMINATE_INTEGRATION', () => {
      action = _.cloneDeep(genericAction);
      action.type = actions.RECEIVE_TERMINATE_INTEGRATION;
      expect(reducers.loadUrl(undefined, action)).toEqual(action.loadUrl);
    });
  });

  describe('error', () => {
    it('should return an object with message and logs as properties', () => {
      action = _.cloneDeep(genericAction);
      action.type = actions.RECEIVE_ERROR
      expect(reducers.error(undefined, action)).toMatchObject({
        message: action.error,
        logs: null,
      });
    });

    const statusError = {
      message: 'Matlab exited with exit code 9',
      logs: 'Java AWT error',
      type: 'java.awt.headlessexception',
    };

    it('should return an error object containing (message, logs and type of error) if there is an error else return null', () => {
      for (let i = 0; i < receiveActions.length; i++) {
        action = _.cloneDeep(genericAction);
        action.type = receiveActions[i];
        action.status.error = null;
        expect(reducers.error(undefined, action)).toBeNull();

        action = _.cloneDeep(genericAction);

        action.type = receiveActions[i];
        action.status.error = statusError;
        expect(reducers.error(undefined, action)).toMatchObject({
          message: action.status.error.message,
          logs: action.status.error.logs,
          type: action.status.error.type,
        });
      }
    });

    it('should return default state', () => {
      action = _.cloneDeep(genericAction);
      expect(reducers.error(undefined, action)).toBeNull();
    });
  });
});
