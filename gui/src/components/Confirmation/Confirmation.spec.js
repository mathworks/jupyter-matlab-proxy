// Copyright 2021 The MathWorks, Inc.

import React from 'react';
import Confirmation from './index';
import App from '../App'
import { render, fireEvent } from '../../test/utils/react-test';

describe('Confirmation Component', () => {
  let children, confirmMock, cancelMock, initialState;
  beforeAll(() => {
    children = (
      <div data-testid="wrapperNode">
        <div data-testid="childNode"></div>
      </div>
    );
    confirmMock = jest.fn().mockImplementation(() => {});
    cancelMock = jest.fn().mockImplementation(() => {});
  });

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
        wsEnv:'mw'
      },
      loadUrl: null,
      error: null,
    };
  });


  afterEach(() => {
    jest.clearAllMocks();
  });

  it('throws console.error when rendered without the required prop types', () => {
    const errorMock = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<Confirmation />);
    // Three required prop types, hence console.error will be called 3 times
    expect(errorMock).toHaveBeenCalledTimes(3);
  });

  it('should be able to render child nodes without crashing', () => {
    const { getByTestId } = render(
      <Confirmation
        children={children}
        confirm={confirmMock}
        cancel={cancelMock}
      />
    );

    expect(getByTestId('wrapperNode')).toBeInTheDocument();
    expect(getByTestId('childNode')).toBeInTheDocument();
  });

  it('should fire onClick Event for confirm and cancel button without crashing', () => {
    const { getByTestId } = render(
      <Confirmation
        children={children}
        confirm={confirmMock}
        cancel={cancelMock}
      />
    );

    expect(getByTestId('wrapperNode')).toBeInTheDocument();

    const confirmButton = getByTestId('confirmButton');
    const cancelButton = getByTestId('cancelButton');

    fireEvent.click(confirmButton);
    expect(confirmMock).toHaveBeenCalledTimes(1);
    fireEvent.click(cancelButton);
    expect(cancelMock).toHaveBeenCalledTimes(1);
  });


  test.each([
    ['confirmButton'], ['cancelButton']])(
    'Test to check if confirmation component disappears when %s is clicked',
    (input) => {

  // Hide the tutorial and make the overlay visible.
    initialState.tutorialHidden = true;
    initialState.overlayVisibility = true;

    const { debug, getByTestId, container } = render(<App />, {
      initialState: initialState,
    });

    let startMatlabButton = getByTestId('startMatlabBtn');
    fireEvent.click(startMatlabButton);

    // Upon clicking on start/restart MATLAB, should display the confirmation component.
    expect(container.querySelector('#confirmation')).toBeInTheDocument();

    const btn = getByTestId(input);
    fireEvent.click(btn);

    // Upon clicking the input button, should return to rendering the Information Component
    // and close the confirmation component
    expect(container.querySelector('#confirmation')).not.toBeInTheDocument();
    }
  );

});
