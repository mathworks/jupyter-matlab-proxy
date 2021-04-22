// Copyright 2020-2021 The MathWorks, Inc.

import React from 'react';
import { render, fireEvent, within } from '../../test/utils/react-test';
import App from './index';
import OverlayTrigger from '../OverlayTrigger';

describe('App Component', () => {
  let initialState;
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
    const mockIntersectionObserver = jest.fn();
    mockIntersectionObserver.mockReturnValue({
      observe: () => null,
      disconnect: () => null,
    });

    window.IntersectionObserver = mockIntersectionObserver;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // it('renders app without crashing', () => {
  //   const { getByTestId } = render(<App />);
  //   expect(getByTestId('app')).toBeInTheDocument();
  // });

  it('should render overlayTrigger (after closing the tutorial)', () => {

    // Hide the tutorial before rendering the component.
    initialState.tutorialHidden = true;

    const { getByTestId } = render(<App />, {
      initialState: initialState,
    });

    //grab the overlayTrigger
    const overlayTriggerComponent = getByTestId(
      'overlayTrigger'
    );

    expect(overlayTriggerComponent).toBeInTheDocument();
  });

  it('should render LicensingGatherer component within the App component when no licensing is provided', () => {

    //Set lincensingInfo to empty object.
    initialState.serverStatus.licensingInfo = {};
    initialState.overlayVisibility = true;

    const { getByRole } = render(<App />, {
      initialState: initialState,
    });

    const licensingGathererComponent = getByRole(
      'document'
    );
    expect(licensingGathererComponent).toBeInTheDocument();
  });

  it('should render Information Component within App Component after licensing is provided', () => {

    // Hide the tutorial and make the overlay visible.
    initialState.tutorialHidden = true;
    initialState.overlayVisibility = true;

    //Rendering the App component with the above changes to the initial
    // state should render the Information Component.
    const { getByRole } = render(<App />, {
      initialState: initialState,
    });

    const informationComponent = getByRole('document');
    expect(informationComponent).toBeInTheDocument();
  });

  it('should display integration terminated error', () => {

    //Hide the tutorial, make the overlay visible and set fetchFailCount to 10
    initialState.tutorialHidden = true;
    initialState.overlayVisibility = true;
    initialState.serverStatus.fetchFailCount = 10;

    //Rendering the App component with above changes to the initial state
    // will terminate the integration.
    const { container } = render(<App />, {
      initialState: initialState,
    });


    const paragraphElements = [...container.getElementsByTagName('p')];


    expect(
      paragraphElements.some((p) =>
        p.textContent.includes('integration terminated')
      )
    ).toBe(true);
  });

  it('should display MatlabInstallError', () => {
    initialState.error = {
      type: 'MatlabInstallError',
      message: 'Matlab Installation error. Exited with status code -9',
    };
    initialState.serverStatus.licensingInfo = {};
    initialState.overlayVisibility = true;

    const { container } = render(<App />, {
      initialState: initialState,
    });

    const paragraphElements = [...container.getElementsByTagName('p')];

    expect(
      paragraphElements.some((p) =>
        p.textContent.includes(initialState.error.message)
      )
    ).toBe(true);
  });

  it('should display Confirmation component ', () => {

    //Hide the tutorial and make the overlay visible
    initialState.tutorialHidden = true;
    initialState.overlayVisibility = true;

    const { getByTestId, container } = render(<App />, {
      initialState: initialState,
    });


    const startMatlabBtn = getByTestId('startMatlabBtn');

    fireEvent.click(startMatlabBtn);

    const confirmMatlabRestart = container
      .getElementsByClassName('modal-body')
      .item(0);

    expect(confirmMatlabRestart.textContent).toMatch('restart MATLAB?');

    const confirmBtn = getByTestId('confirmButton');
    expect(confirmBtn).toBeInTheDocument();
  });

  it('should display Help Component', () => {

    //Hide the tutorial and make the overlay visible
    initialState.tutorialHidden = true;
    initialState.overlayVisibility = true;

    const {  getByTestId, container, getByRole } = render(<App />, {
      initialState: initialState,
    });


    // Grab the help button and click it.
    const helpBtn = getByTestId('helpBtn');
    fireEvent.click(helpBtn);

    const helpElement = container.querySelector('#confirmation-dialog-title');

    expect(helpElement.textContent).toMatch('Help');
  });

  it('should set the window location from state', () => {
    initialState.loadUrl = 'http://localhost.com:5555';
    const hrefMock = jest.fn();
    delete window.location;

    window.location = {href : hrefMock}
    const { debug } = render(<App />, { initialState: initialState });

    expect(window.location.href).toMatch('localhost');
  });
});
