// Copyright 2021 The MathWorks, Inc.

import React from 'react';
import Controls from './index';
import App from '../App'
import { render, fireEvent } from '../../test/utils/react-test';

describe('Controls Component', () => {
  let initialState, callbackFn;

  beforeEach(() => {
    initialState = {
      triggerPosition: { x: 539, y: 0 },
      tutorialHidden: false,
      overlayVisibility: false,
      serverStatus: {
        licensingInfo: { type: 'MHLM', emailAddress: 'abc@mathworks.com' },
        matlabStatus: 'up',
        matlabVersion: 'R2020b',
        isFetching: false,
        hasFetched: true,
        isSubmitting: false,
        fetchAbortController: new AbortController(),
        fetchFailCount: 0,
      },
      loadUrl: null,
      error: null,
    };

    callbackFn = jest.fn().mockImplementation((confirmationType) => {});
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render without crashing', () => {
    render(<Controls callback={callbackFn} />);
  });

  it('should startMatlab on button click', () => {
    const { debug, getByTestId } = render(<Controls callback={callbackFn} />, {
      initialState: initialState,
    });

    const btn = getByTestId('startMatlabBtn');
    fireEvent.click(btn);

    expect(callbackFn).toHaveBeenCalledTimes(1);
  });

  it('should stopMatlab on button click', () => {
    const { debug, getByTestId } = render(<Controls callback={callbackFn} />, {
      initialState: initialState,
    });

    const btn = getByTestId('stopMatlabBtn');
    fireEvent.click(btn);

    expect(callbackFn).toHaveBeenCalledTimes(1);
  });

  it('should unsetLicensing on button click', () => {
    const { debug, getByTestId } = render(<Controls callback={callbackFn} />, {
      initialState: initialState,
    });

    const btn = getByTestId('unsetLicensingBtn');
    fireEvent.click(btn);

    expect(callbackFn).toHaveBeenCalledTimes(1);
  });
  it('should open Help on button click', () => {
    const { debug, getByTestId } = render(<Controls callback={callbackFn} />, {
      initialState: initialState,
    });

    const btn = getByTestId('helpBtn');
    fireEvent.click(btn);

    expect(callbackFn).toHaveBeenCalledTimes(1);
  });

  it('should render additional css style when error', () => {
    initialState.error = {
      type: 'OnlineLicensingError',
    };

    const { getByTestId } = render(<Controls callback={callbackFn} />, {
      initialState: initialState,
    });

    const btn = getByTestId('startMatlabBtn');
    expect(btn).toHaveClass('btn_color_blue');
  });

  it('should restart matlab upon clicking the Start/Restart Matlab button', () => {

    //Hide the tutorial and make the overlay visible.
    initialState.tutorialHidden = true;
    initialState.overlayVisibility = true;

    const { getByTestId, container } = render(<App />, {
      initialState: initialState,
    });

    const startMatlabButton = getByTestId('startMatlabBtn');
    fireEvent.click(startMatlabButton);

    expect(container.querySelector('#confirmation')).toBeInTheDocument();

    const confirmButton = getByTestId('confirmButton');
    fireEvent.click(confirmButton);

    let tableData = container.querySelector('.details');
    expect(tableData.innerHTML).toMatch('Running');
  });

});
