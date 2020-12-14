// Copyright 2020 The MathWorks, Inc.

import * as reducers from './index';
import * as actions from '../actions';

describe('reducers', () => {

    describe('overlayVisibility', () => {

        it('should return the intial state', () => {
            expect(
                reducers.overlayVisibility(undefined, {})
            ).toEqual(
                false
            );
        });

        it('should handle SET_OVERLAY_VISIBILITY', () => {
            // Set visibility to true
            expect(
                reducers.overlayVisibility(
                    undefined,
                    {
                        type: actions.SET_OVERLAY_VISIBILITY,
                        visibility: true
                    }
                )
            ).toEqual(
                true
            );

            // Then set visibility to false
            expect(
                reducers.overlayVisibility(
                    undefined,
                    {
                        type: actions.SET_OVERLAY_VISIBILITY,
                        visibility: false
                    }
                )
            ).toEqual(
                false
            );
        });

    });

});