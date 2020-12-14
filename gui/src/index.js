// Copyright 2020 The MathWorks, Inc.

import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, compose } from 'redux';
import './index.css';
import App from './components/App';
// import * as serviceWorker from './serviceWorker';
import rootReducer from './reducers';
import thunkMiddleware from 'redux-thunk';

const composeEnhancers = (
    typeof window !== 'undefined'
    && window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__
) || compose;

const store = createStore(rootReducer, composeEnhancers(
    applyMiddleware(thunkMiddleware)
));

ReactDOM.render(
    <Provider store={store}>
        <App />
    </Provider>,
    document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
// serviceWorker.unregister();
