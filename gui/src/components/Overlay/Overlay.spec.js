// Copyright 2021 The MathWorks, Inc.

import React from 'react';
import Overlay from './index';
import { render } from '../../test/utils/react-test';

describe('Overlay Component', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render without crashing and passes the style property to the div', () => {
    const { container, rerender } = render(<Overlay />);

    //Check if attribute style is not present in the rendered div
    let overlayDiv = container.querySelector('#overlay');

    expect(overlayDiv).toHaveStyle('backgroundColor: false');

    rerender(<Overlay transparent={true} />);
    overlayDiv = container.querySelector('#overlay');
    expect(overlayDiv).toHaveStyle('backgroundColor: true');
  });
});
