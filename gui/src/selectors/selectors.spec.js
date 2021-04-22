// Copyright 2020-2021 The MathWorks, Inc.

import * as selectors from './index';
const _ = require('lodash');

describe('selectors', () => {
  let modifiedState;
  let state = {
      overlayVisibility: true,
      triggerPosition: {
        x: 12,
        y: 12,
      },
      tutorialHidden: true,
      loadUrl: '/',
      error: null,
      serverStatus: {
        matlabStatus: 'up',
        matlabVersion: 'R2020b',
        isSubmitting: true,
        hasFetched: false,
        licensingInfo: {
          type: 'MHLM',
          emailAddress: 'abc@mathworks.com',
        },
        fetchFailCount: 2,
        fetchAbortController: new AbortController(),
      },
    };

    const { tutorialHidden,
            serverStatus,
            loadUrl,
            error
          } = state;

    const { matlabVersion,
            isSubmitting,
            hasFetched,
            licensingInfo,
            fetchFailCount,
            matlabStatus,
            fetchAbortController,
          } = state.serverStatus;


  const {
    selectTutorialHidden,
    selectServerStatus,
    selectLoadUrl,
    selectError,
    selectMatlabStatus,
    selectMatlabVersion,
    selectSubmittingServerStatus,
    selectHasFetchedServerStatus,
    selectLicensingInfo,
    selectServerStatusFetchFailCount,
    selectTriggerPosition,
    selectIsError,
    selectIsConnectionError,
    selectMatlabUp,
    selectMatlabRunning,
    selectOverlayHidable,
    selectOverlayVisibility,
    getFetchAbortController,
    selectFetchStatusPeriod,
    selectLicensingProvided,
    selectLicensingIsMhlm,
    selectLicensingMhlmUsername,
    selectMatlabPending,
    selectOverlayVisible,
    selectInformationDetails,
  } = selectors;

  // beforeAll(() => {
  //   // modifiedState = JSON.parse(JSON.stringify(state));
  //   // modifiedState.triggerPosition = null;
  // });


  describe.each([
   [selectTutorialHidden, tutorialHidden],
   [selectServerStatus, serverStatus],
   [selectLoadUrl, loadUrl],
   [selectError, error],
   [selectMatlabVersion, matlabVersion],
   [selectMatlabStatus, matlabStatus],
   [selectSubmittingServerStatus, isSubmitting],
   [selectHasFetchedServerStatus, hasFetched],
   [selectLicensingInfo, licensingInfo],
   [selectServerStatusFetchFailCount, fetchFailCount],
   [getFetchAbortController, fetchAbortController]
  ])
    ('Test simple selectors',
      (selector, expected) => {
        test(`Check if ${selector.name} selects piece of state`, () => {
          expect(selector(state)).toBe(expected);
        });
      }
    );




describe('Test derived selectors', () => {

  test('selectTriggerPosition return position for valid trigger position', () => {
    expect(selectTriggerPosition(state)).toEqual(state.triggerPosition);

    modifiedState = _.cloneDeep(state);
    modifiedState.triggerPosition = null;

    expect(selectTriggerPosition(modifiedState)).toBeUndefined();
  });

  test('selectTriggerPosition return undefined for invalid trigger position', () => {
    modifiedState = _.cloneDeep(state);
    modifiedState.triggerPosition = null;

    expect(selectTriggerPosition(modifiedState)).toBeUndefined();
  });

  test('selectIsError should return false when no error', () => {
    expect(selectIsError(state)).toBe(false);
  });

  test('selectIsError should return true when  error', () => {
    modifiedState = _.cloneDeep(state);
    modifiedState.error = { };

    expect(selectIsError(modifiedState)).toBe(true);
  });

  test('selectIsConnectionError should return false when fetch fail count is < 5', () => {
    expect(selectIsConnectionError(state)).toBe(false);
  })

  test('selectIsConnectionError should return true when fetch fail count is >= 5', () => {

    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.fetchFailCount = 10;
    expect(selectIsConnectionError(modifiedState)).toBe(true);
  });

  test('selectMatlabUp should return true when Matlab is up', () => {
    expect(selectMatlabUp(state)).toBe(true);
  });

  test('selectMatlabUp should false when Matlab status is not up', () => {

    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.matlabStatus = 'down';
    expect(selectMatlabUp(modifiedState)).toBe(false);
  });


  test('selectMatlabRunning should return true when Matlab is up or starting', () => {
    expect(selectMatlabRunning(state)).toBe(true);
    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.matlabStatus = 'starting';
    expect(selectMatlabRunning(modifiedState)).toBe(true);
  });

  test('selectMatlabRunning should false when Matlab status is not up or starting', () => {

    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.matlabStatus = 'down';
    expect(selectMatlabRunning(modifiedState)).toBe(false);
  });

  test('selectOverlayHidable should return true when matlab is up and there is no error ', () => {
    expect(selectOverlayHidable(state)).toBe(true);
  });

  test('selectOverlayHidable should return false when matlab is not up or there is an error ', () => {
    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.matlabStatus = 'down';
    expect(selectOverlayHidable(modifiedState)).toBe(false);

    modifiedState = _.cloneDeep(state);
    modifiedState.error = {};
    expect(selectOverlayHidable(modifiedState)).toBe(false);
  });


  test('selectOverlayVisibility should return true when matlab is not up or visibility is true or there is an error ', () => {
    //Should return true based on state.overlayVisibility
    expect(selectOverlayVisibility(state)).toBe(true);

    //should return true based on matlabStatus
    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.matlabStatus = 'down';
    modifiedState.overlayVisibility = false;
    expect(selectOverlayVisibility(modifiedState)).toBe(true);

    //should return true based on error
    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.matlabStatus = 'down';
    modifiedState.overlayVisibility = false;
    modifiedState.error = {};
    expect(selectOverlayVisibility(modifiedState)).toBe(true);
  });

  test('selectOverlayVisibility should return false when matlab is up and visibility is false and there is no error ', () => {
    //Should return false matlab is up and overlayVisibility is false and there is an error
    modifiedState = _.cloneDeep(state);
    modifiedState.overlayVisibility = false;
    expect(selectOverlayVisibility(modifiedState)).toBe(false);
  });

  test('selectFetchStatusPeriod should return null if submitting to server', () => {
        expect(selectFetchStatusPeriod(state)).toBeNull();
  });

  test('selectFetchStatusPeriod should return 10000ms when matlab is up ', () => {
    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.isSubmitting = false;
    expect(selectFetchStatusPeriod(modifiedState)).toBe(10000);
  })

  test.each([
    ['starting'],
    ['down']
  ])(
    'selectFetchStatusPeriod should return 500ms when matlab %s (ie. not up)',
    (input) => {

      modifiedState = _.cloneDeep(state);
      modifiedState.serverStatus.isSubmitting = false;
      modifiedState.serverStatus.matlabStatus = input;

      expect(selectFetchStatusPeriod(modifiedState)).toBe(5000);
    }
  );

  test('selectLicensingProvided should return true if licensingInfo has property type else false', () => {
    expect(selectLicensingProvided(state)).toBe(true);

    modifiedState = _.cloneDeep(state);
    delete modifiedState.serverStatus.licensingInfo.type;

    expect(selectLicensingProvided(modifiedState)).toBe(false);
  });

  test('selectLicensingIsMhlm should return true is licensing is of type MHLM', () => {
     expect(selectLicensingIsMhlm(state)).toBe(true);
  });


  test('selectLicensingIsMhlm should return false is licensing is not of type MHLM', () => {
    modifiedState = _.cloneDeep(state);
    delete modifiedState.serverStatus.licensingInfo.type;
    expect(selectLicensingIsMhlm(modifiedState)).toBe(false);

    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.licensingInfo.type = "NLM";
    expect(selectLicensingIsMhlm(modifiedState)).toBe(false);
  });


  test('selectLicensingMhlmUsername should return the email address if licensing is of type MHLM', () => {
    expect(selectLicensingMhlmUsername(state)).toBe(state.serverStatus.licensingInfo.emailAddress)
  });


  test('selectLicensingMhlmUsername should return empty string if licensing is not of type MHLM', () => {
    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.licensingInfo.type = 'NLM';
    expect(selectLicensingMhlmUsername(modifiedState)).toBe('');
  });

  test('selectMatlabPending should true if matlabStatus is starting, false otherwise ', () => {
    expect(selectMatlabPending(state)).toBe(false);

    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.matlabStatus = 'starting';
    expect(selectMatlabPending(modifiedState)).toBe(true);
  });

  test('selectOverlayVisible should return true if selectOverlayVisibility is true or if there is any error', () => {
    // When overlay is visible and no error
    expect(selectOverlayVisible(state)).toBe(true);

      modifiedState = _.cloneDeep(state);
      modifiedState.overlayVisibility = false;
      modifiedState.error = {}

      // when overlay is not visible and error is not null
      expect(selectOverlayVisibility(modifiedState)).toBe(true);

      modifiedState = _.cloneDeep(state);
      modifiedState.error = {}
      // when overlay is visible and there is an error
      expect(selectOverlayVisibility(modifiedState)).toBe(true);

  });

   test('selectOverlayVisible should return false if selectOverlayVisibility is false and if there is no error', () => {
    modifiedState = _.cloneDeep(state);
    modifiedState.overlayVisibility = false;
  });

  test('For any other MatlabStatus  selectInformationDetails should throw an error', () => {
    modifiedState = _.cloneDeep(state);
    modifiedState.serverStatus.matlabStatus = 'defaultCase';

    expect(() => selectInformationDetails(modifiedState)).toThrow(Error);
  })

  test('For MatlabStatus down and with an error, selectInformationDetails should return object with icon error', () => {
    modifiedState = _.cloneDeep(state);
    modifiedState.error = {};
    modifiedState.serverStatus.matlabStatus = 'down';

    expect(selectInformationDetails(modifiedState).icon.toLowerCase()).toContain('error');
  })

  describe.each([
    ['up', 'running'],
    ['starting', 'starting'],
    ['down', 'not running'],

  ])(
      'SelectInformationDetails',
      (input, expected) => {

        beforeAll(() => {
          modifiedState = _.cloneDeep(state);
          modifiedState.serverStatus.matlabStatus = input;
        });
        test(`For MatlabStatus ${input}, selectInformationDetails should return object with label which contains: ${expected}`, () => {
          expect(selectInformationDetails(modifiedState).label.toLowerCase()).toContain(expected);
        });
      }
    );
  });
});
