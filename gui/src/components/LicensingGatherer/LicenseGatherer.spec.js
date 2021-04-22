// Copyright 2021 The MathWorks, Inc.

import React from 'react';
import LicenseGatherer from './index';
import { render, fireEvent } from '../../test/utils/react-test';
import fetchMock from 'fetch-mock';

describe('LicenseGatherer component', () => {

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
        wsEnv: 'abcd',
      },
      loadUrl: null,
      error: null,
    };

  });

  afterEach(() => {
    jest.clearAllMocks();
  });


  it('should throw error', () => {

    const errorMock = jest.spyOn(console, 'error').mockImplementation(() => {})

    try{
      render(<LicenseGatherer />);
    }
    catch(error){
      expect(error).toBeInstanceOf(TypeError);
      expect(errorMock).toHaveBeenCalledTimes(2);
    }

  });

  it('should render without crashing', () => {
    render(<LicenseGatherer />, {initialState: initialState});
  });


  it('should render without crashing. Should have a subdomain for mhlmLoginHostName', () => {

    initialState.serverStatus.wsEnv = 'mw-integ'

    const {container, debug} = render(<LicenseGatherer />, {initialState: initialState});

    const mhlmTab = container.querySelector('#mhlm-tab');

    expect(mhlmTab).toBeInTheDocument();

    fireEvent.click(mhlmTab);

    const iFrame = container.getElementsByTagName('iframe').item(0)

    expect(iFrame.src).toContain(initialState.serverStatus.wsEnv);
  });

  it('should have rendered mhlm tab by default without crashing', () => {
    const { container } = render(<LicenseGatherer />, {initialState: initialState});

    const mhlmTab = container.querySelector('#mhlm-tab');

    expect(mhlmTab).toBeInTheDocument();
    // Click on mhlm Tab
    fireEvent.click(mhlmTab);

    // Check if mhlm iframe is rendered.
    const mhlmTabContent = container.querySelector('#MHLM');
    expect(mhlmTabContent).toBeInTheDocument();
  });

  it('should have rendered nlm tab content without crashing', () => {
    const { container } = render(<LicenseGatherer />, {initialState: initialState});

    const nlmTab = container.querySelector('#nlm-tab');
    expect(nlmTab).toBeInTheDocument();

    // Click on nlm Tab
    fireEvent.click(nlmTab);

    // Check if nlm iframe is rendered.
    const nlmTabContent = container.querySelector('#NLM');
    expect(nlmTabContent).toBeInTheDocument();
  });
});
