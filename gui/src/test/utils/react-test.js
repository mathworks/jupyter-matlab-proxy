// Copyright 2020 The MathWorks, Inc.

import React from 'react';
import { render as rtlRender } from '@testing-library/react';
import { createStore, applyMiddleware, compose } from 'redux';
import { Provider } from 'react-redux';
import thunkMiddleware from 'redux-thunk';
import reducer from '../../reducers';

function render(
  ui,
  {
    initialState,
    store = createStore(
      reducer,
      initialState,
      compose(applyMiddleware(thunkMiddleware))
    ),
    ...renderOptions
  } = {}
) {
  function Wrapper({ children }) {
    return <Provider store={store}>{children}</Provider>;
  }
  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
}

export * from '@testing-library/react';
export { render };