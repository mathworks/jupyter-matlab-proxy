// Copyright 2026 The MathWorks, Inc.

import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';

import { ICommunicationChannel } from '../matlabCommunication';
import { BaseAction } from './baseAction';
import { ActionTypes } from './actionTypes';
import { isCommValid } from './actionUtils';

export class CheckFileExistsAction extends BaseAction {
    private static blockingPromise: PromiseDelegate<ReadonlyJSONValue> | null;
    private static fileExists: boolean = false;

    constructor (blocking: boolean) {
        super();
        this.blocking = blocking;
    }

    public getActionName (): string {
        return ActionTypes.CHECK_FILE_EXISTS;
    }

    public static getFileExistsStatus (): boolean {
        return CheckFileExistsAction.fileExists;
    }

    public async execute (data: any, comm: ICommunicationChannel): Promise<void> {
        if (!('ipynbFilePath' in data)) {
            console.error('Missing data for executing CheckFileExists action...');
            return;
        }

        if (!CheckFileExistsAction.blockingPromise) {
            CheckFileExistsAction.blockingPromise =
        new PromiseDelegate<ReadonlyJSONValue>();
        }

        if (this.sendCheckFileExistsRequest(data.ipynbFilePath, comm)) {
            console.debug('Successfully sent check file exists request to kernel.');
        } else {
            console.error('Failed to send check file exists request to kernel.');
        }

        if (this.blocking) {
            console.debug(
                'CheckFileExists blocking action will wait for promise to resolve...'
            );
            await CheckFileExistsAction.blockingPromise.promise;
        }

        console.debug('CheckFileExistsAction execute completed');
    }

    public onMsg (data: any, _: ICommunicationChannel): void {
        if ('error' in data && data.error) {
            console.error('Received error from kernel ', data.error);
            if (CheckFileExistsAction.blockingPromise) {
                CheckFileExistsAction.blockingPromise.reject({ reason: data.error });
                CheckFileExistsAction.blockingPromise = null;
            }
            return;
        }
        CheckFileExistsAction.fileExists = data.exists;

        if (CheckFileExistsAction.blockingPromise) {
            CheckFileExistsAction.blockingPromise.resolve(null);
            CheckFileExistsAction.blockingPromise = null;
        }

        console.debug('CheckFileExistsAction onMsg completed');
    }

    private sendCheckFileExistsRequest (
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
            action: ActionTypes.CHECK_FILE_EXISTS,
            data: {
                ipynbFilePath: filePath
            }
        });
        return true;
    }
}
