// Copyright 2025-2026 The MathWorks, Inc.

import { ActionFactory } from '../../../plugins/actions/actionFactory';
import { ActionTypes } from '../../../plugins/actions/actionTypes';
import { BaseAction } from '../../../plugins/actions/baseAction';
import { ConvertAction } from '../../../plugins/actions/convertAction';
import { EditAction } from '../../../plugins/actions/editAction';
import { MatlabStatusAction } from '../../../plugins/actions/matlabStatusAction';
import { StartMatlabProxyAction } from '../../../plugins/actions/startMatlabProxyAction';
import { CheckFileExistsAction } from '../../../plugins/actions/checkFileExistsAction';

describe('ActionFactory', () => {
    describe('createAction', () => {
        it('should create the correct action class for each action type', () => {
            const actionTypeToClass = [
                { type: ActionTypes.CONVERT, expectedClass: ConvertAction },
                { type: ActionTypes.EDIT, expectedClass: EditAction },
                { type: ActionTypes.MATLAB_STATUS, expectedClass: MatlabStatusAction },
                { type: ActionTypes.START_MATLAB_PROXY, expectedClass: StartMatlabProxyAction },
                { type: ActionTypes.CHECK_FILE_EXISTS, expectedClass: CheckFileExistsAction }
            ];

            actionTypeToClass.forEach(({ type, expectedClass }) => {
                const action = ActionFactory.createAction(type, true);

                expect(action).toBeInstanceOf(expectedClass);
                expect(action).toBeInstanceOf(BaseAction);
            });
        });

        it('should throw error for UNKNOWN action type', () => {
            expect(() => {
                ActionFactory.createAction(ActionTypes.UNKNOWN, true);
            }).toThrow('Unknown action type: unknown');
        });

        it('should pass blocking parameter to action', () => {
            const blockingAction = ActionFactory.createAction(
                ActionTypes.EDIT,
                true
            ) as EditAction;

            const nonBlockingAction = ActionFactory.createAction(
                ActionTypes.EDIT,
                false
            ) as EditAction;

            expect(blockingAction.blocking).toBe(true);
            expect(nonBlockingAction.blocking).toBe(false);
        });
    });

    describe('action interface compliance with base action class', () => {
        const actionTypes = [
            ActionTypes.CONVERT,
            ActionTypes.EDIT,
            ActionTypes.MATLAB_STATUS,
            ActionTypes.START_MATLAB_PROXY,
            ActionTypes.CHECK_FILE_EXISTS
        ];

        actionTypes.forEach((actionType) => {
            it(`should create action with execute method for ${actionType}`, () => {
                const action = ActionFactory.createAction(
                    actionType,
                    true
                );

                expect(typeof action.execute).toBe('function');
            });

            it(`should create action with onMsg method for ${actionType}`, () => {
                const action = ActionFactory.createAction(
                    actionType,
                    true
                );

                expect(typeof action.onMsg).toBe('function');
            });

            it(`should create action with getActionName method for ${actionType}`, () => {
                const action = ActionFactory.createAction(
                    actionType,
                    true
                );

                expect(typeof action.getActionName).toBe('function');
                expect(action.getActionName()).toBe(actionType);
            });
        });
    });
});
