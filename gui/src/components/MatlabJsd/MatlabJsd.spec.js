// Copyright 2020 The MathWorks, Inc.

import React from 'react';
import ReactDOM from 'react-dom';
import MatlabJsd from './index';

it('renders without crashing', () => {
    const div = document.createElement('div');
    // Intentionally use illegal port number so that the iframe content page
    // will never be found (this can slow down the test dramatically)
    ReactDOM.render(<MatlabJsd url={"http://localhost:65536"} />, div);
});
