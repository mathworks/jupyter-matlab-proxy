// Copyright 2020-2021 The MathWorks, Inc.

import React from 'react';
import MatlabJsd from './index';
import { render } from '../../test/utils/react-test';

describe('MatlabJsd Component', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('throws console.error when rendered without required prop-type', () => {
    // Mocking console.error to do nothing.
    const errorMessage = ['Warning: Failed prop type: The prop `url` is marked as required in `MatlabJsd`, but its value is `undefined`.\n    in MatlabJsd'];
    const errorMock = jest.spyOn(console, 'error').mockImplementation(() => {});

    const { queryByTitle } = render(<MatlabJsd />);

    // Check if attribute 'src' is not present in the rendered iFrame
    const iFrame = queryByTitle('MATLAB JSD');
    expect(iFrame).not.toHaveAttribute('src');

    // Check if console.error has been called 1 time.
    expect(errorMock).toHaveBeenCalledTimes(1);

    // Check if console.error was called with the correct error message.
    expect(console.error.mock.calls).toEqual([errorMessage]);
  });

  it('renders without crashing', () => {
    const { queryByTitle, container } = render(
      <MatlabJsd url={'http://localhost:3000'} />
    );

    // Check if div is rendered
    expect(container.querySelector('#MatlabJsd')).toBeInTheDocument();

    // Check if url is passed to the iFrame
    const iFrame = queryByTitle('MATLAB JSD');
    expect(iFrame).toHaveAttribute('src');
  });
});
