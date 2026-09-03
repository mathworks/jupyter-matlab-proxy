// Copyright 2026 The MathWorks, Inc.

import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';

import { BaseAction } from './baseAction';
import { ActionTypes } from './actionTypes';
import { ICommunicationChannel } from '../matlabCommunication';
import { isCommValid } from './actionUtils';

export class EditAction extends BaseAction {
    private static blockingPromise: PromiseDelegate<ReadonlyJSONValue> | null;

    constructor (blocking: boolean) {
        super();
        this.blocking = blocking;
    }

    public getActionName (): string {
        return ActionTypes.EDIT;
    }

    public async execute (data: any, comm: ICommunicationChannel): Promise<void> {
        console.debug('EditAction execute called with data ', data);

        // Send edit request to kernel only if liveCodeFilePath is available
        if ('liveCodeFilePath' in data) {
            this.sendEditRequest(data.liveCodeFilePath, comm);
        } else {
            const errMsg = 'liveCodeFilePath missing for sending edit request';
            console.error(errMsg);
            return;
        }

        if (!EditAction.blockingPromise) {
            EditAction.blockingPromise = new PromiseDelegate<ReadonlyJSONValue>();
        }

        if (this.blocking) {
            console.debug(
                'This is a blocking action will wait for promise to resolve...'
            );
            await EditAction.blockingPromise.promise;
        }

        console.debug('EditAction execute completed');
    }

    public onMsg (data: any, _: ICommunicationChannel): void {
        if ('error' in data && data.error) {
            console.error('Received error from kernel ', data.error);
            if (EditAction.blockingPromise) {
                EditAction.blockingPromise.reject({ reason: data.error });
                EditAction.blockingPromise = null;
            }
            return;
        }
        // Nothing to handle after sending the edit command to the kernel...
        if (EditAction.blockingPromise) {
            EditAction.blockingPromise.resolve(null);
        }

        console.debug('EditAction onMsg completed');
    }

    private sendEditRequest (
        filePath: string,
        comm: ICommunicationChannel
    ): boolean {
        if (!isCommValid(comm)) {
            console.error('Communication channel is not available');
            return false;
        }

        if (!filePath) {
            console.error('File path is not available');
            return false;
        }

        comm.send({
            action: ActionTypes.EDIT,
            data: {
                liveCodeFilePath: filePath
            }
        });
        return true;
    }
}
