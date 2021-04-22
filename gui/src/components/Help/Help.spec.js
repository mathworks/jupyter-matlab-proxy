// Copyright 2021 The MathWorks, Inc.

import React from 'react';
import App from '../App'
import Help from './index';
import { render, fireEvent } from '../../test/utils/react-test';

describe('Help Component', () => {
  let closeHandler, initialState;
  beforeEach(() => {
    closeHandler = jest.fn().mockImplementation(() => {});
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
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  it('should throw console.error for not passing in prop types', () => {
    const errorMock = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<Help />);
    expect(errorMock).toHaveBeenCalledTimes(1);
  });

  it('should render without crashing', () => {
     render(<Help closeHandler={closeHandler} />);
  });

  it('should fire onClose event of Help modal when Back button is clicked', () => {
    const { getByTestId } = render(
      <Help closeHandler={closeHandler} />
    );

    const backButton = getByTestId('backBtn');

    fireEvent.click(backButton);

    expect(closeHandler).toHaveBeenCalledTimes(1);
  });


  it('should close the Help Modal and display Information component when Back button is clicked', () => {

    // Hide the tutorial and make the overlay visible.
    initialState.tutorialHidden = true;
    initialState.overlayVisibility = true;

    //Rendering the App component with the above changes to the initial
    // state should render the Information Component.
    const { getByTestId, container } = render(<App />, {
      initialState: initialState,
    });


    // Grab and click on the Help Button
    const helpButton = getByTestId('helpBtn');
    fireEvent.click(helpButton);

    const helpComponent = container.querySelector('#help');

    // Check if Help dialog is rendered.
    expect(helpComponent).toBeInTheDocument();

    // Grab and click on the Back button in the help Component.
    const backButton =  getByTestId('backBtn');
    fireEvent.click(backButton);

    //The Help dialog should disappear
    expect(helpComponent).not.toBeInTheDocument();


  });

  it('should call onClick function', () => {
    const { getByRole } = render(
      <Help closeHandler={closeHandler} dismissAllHandler={closeHandler} />,
      { initialState: initialState }
    );

    const modal = getByRole('dialog');

    fireEvent.click(modal);

    expect(closeHandler).toHaveBeenCalledTimes(1);
  });
});
