// Copyright 2026 The MathWorks, Inc.

import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';
import { ICommunicationChannel } from '../matlabCommunication';
import { BaseAction } from './baseAction';
import { ActionTypes } from './actionTypes';
import { displayConversionNotification, displayUnsupportedMatlabVersionNotification } from '../../utils/notifications';
import { isCommValid } from './actionUtils';

export class ConvertAction extends BaseAction {
    private static liveCodeFilePath: string;
    private static blockingPromise: PromiseDelegate<ReadonlyJSONValue> | null;

    constructor (blocking: boolean) {
        super();
        this.blocking = blocking;
    }

    public getActionName (): string {
        return ActionTypes.CONVERT;
    }

    public static getGeneratedLiveCodeFilePath (): string {
        return ConvertAction.liveCodeFilePath;
    }

    public async execute (data: any, comm: ICommunicationChannel): Promise<void> {
        if (!isCommValid(comm)) {
            console.error('Communication channel is not available');
            return;
        }

        const timeout = 50000;

        comm.send({
            action: this.getActionName(),
            data
        });
        ConvertAction.blockingPromise = displayConversionNotification(timeout);

        if (this.blocking) {
            console.debug(
                'This is a blocking action will wait for promise to resolve...'
            );
            await ConvertAction.blockingPromise.promise;
        }
        console.debug('ConvertAction execute completed');
    }

    public onMsg (data: any, _: ICommunicationChannel): void {
        console.debug('Received data for convert action from kernel ', data);

        // Update data only if there are no errors
        if ('error' in data && data.error) {
            console.error('Received error from kernel ', data.error);

            if (String(data.error).includes('MATLABVersionUnsupportedForConversionError')) {
                displayUnsupportedMatlabVersionNotification();
            }

            if (ConvertAction.blockingPromise) {
                ConvertAction.blockingPromise.reject(new Error(data.error));
                ConvertAction.blockingPromise = null;
            }
            return;
        } else {
            ConvertAction.liveCodeFilePath = data.liveCodeFilePath;
        }

        // Resolve the promise to update the Notification on the UI to 'success' state.
        if ('liveCodeFilePath' in data && data.liveCodeFilePath) {
            if (ConvertAction.blockingPromise) {
                console.debug('liveCodeFilePath in data. resolving promise..');
                // The promise resolved here will allow the execute() function to complete
                ConvertAction.blockingPromise.resolve(null);

                // Update the generated liveCodeFilePath. This will be used by the caller
                // for sending an edit action to open the generated file in the editor.
                ConvertAction.liveCodeFilePath = data.liveCodeFilePath;

                // Set this to null inorder to not reject the promise after timeout.
                ConvertAction.blockingPromise = null;
            }
        } else {
            const errMsg = 'Did not receive liveCodeFilePath in data from kernel';
            console.error(errMsg);
            if (ConvertAction.blockingPromise) {
                ConvertAction.blockingPromise.reject(new Error(errMsg));
                ConvertAction.blockingPromise = null;
            }
        }

        console.debug('ConvertAction onMsg completed');
    }
}
