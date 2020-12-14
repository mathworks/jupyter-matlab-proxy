// Copyright 2020 The MathWorks, Inc.

import React from 'react';
import { render } from '../../test/utils/react-test';
import App from './index';

test('renders app to document', () => {
  const { getByTestId } = render(<App />);
  expect(getByTestId("app")).toBeInTheDocument();
});
