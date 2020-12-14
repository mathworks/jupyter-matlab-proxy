// Copyright 2020 The MathWorks, Inc.

import * as selectors from './index';

describe('selectors', () => {
    it('selectServerStatus', () => {
        expect(
            selectors.selectServerStatus({
                serverStatus: 'down'
            })
        ).toEqual(
            'down'
        );
    });
});