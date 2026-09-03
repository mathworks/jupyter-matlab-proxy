// Copyright 2026 The MathWorks, Inc.

import { ActionTypes } from '../../../plugins/actions/actionTypes';

describe('ActionTypes', () => {
    it('should have correct values for all action types', () => {
        const expectedActionTypes = [
            { key: 'CONVERT', value: 'convert' },
            { key: 'EDIT', value: 'edit' },
            { key: 'MATLAB_STATUS', value: 'matlab_status' },
            { key: 'START_MATLAB_PROXY', value: 'start_matlab_proxy' },
            { key: 'CHECK_FILE_EXISTS', value: 'check_file_exists' },
            { key: 'UNKNOWN', value: 'unknown' }
        ];

        expectedActionTypes.forEach(({ key, value }) => {
            expect(ActionTypes[key as keyof typeof ActionTypes]).toBe(value);
        });
    });

    it('should have exactly 6 action types', () => {
        const actionTypeValues = Object.values(ActionTypes);
        expect(actionTypeValues).toHaveLength(6);
    });

    it('should have all action types as strings', () => {
        Object.values(ActionTypes).forEach((value) => {
            expect(typeof value).toBe('string');
        });
    });
});
