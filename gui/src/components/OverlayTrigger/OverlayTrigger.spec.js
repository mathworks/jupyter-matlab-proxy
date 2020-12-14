// Copyright 2020 The MathWorks, Inc.

import { render } from '../../test/utils/react-test';
import React from 'react';
import OverlayTrigger from './index';

it('renders without crashing', () => {
    render(
        <OverlayTrigger/>
    );
});

it('is shown', () => {
    const { getByTitle } = render(
        <OverlayTrigger
            visible={true}
            toggleVisible={() => null}
            hidable={false}
        />
    );
    expect(
        getByTitle('tools icon')
    ).toBeInTheDocument();
});
