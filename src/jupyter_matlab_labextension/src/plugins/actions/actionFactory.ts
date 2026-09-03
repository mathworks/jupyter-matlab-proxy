// Copyright 2026 The MathWorks, Inc.

import { BaseAction } from './baseAction';
import { ActionTypes } from './actionTypes';

import { ConvertAction } from './convertAction';
import { EditAction } from './editAction';
import { MatlabStatusAction } from './matlabStatusAction';
import { StartMatlabProxyAction } from './startMatlabProxyAction';
import { CheckFileExistsAction } from './checkFileExistsAction';

export class ActionFactory {
    static createAction (
        actionType: string,
        blocking: boolean
    ): BaseAction {
        switch (actionType) {
            case ActionTypes.CONVERT:
                return new ConvertAction(blocking);

            case ActionTypes.EDIT:
                return new EditAction(blocking);

            case ActionTypes.MATLAB_STATUS:
                return new MatlabStatusAction(blocking);

            case ActionTypes.START_MATLAB_PROXY:
                return new StartMatlabProxyAction(blocking);

            case ActionTypes.CHECK_FILE_EXISTS:
                return new CheckFileExistsAction(blocking);

            default:
                throw new Error(`Unknown action type: ${actionType}`);
        }
    }
}
