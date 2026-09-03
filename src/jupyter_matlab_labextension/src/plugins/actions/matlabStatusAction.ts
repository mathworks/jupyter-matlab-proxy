// Copyright 2026 The MathWorks, Inc.

import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';

import { ICommunicationChannel } from '../matlabCommunication';
import { BaseAction } from './baseAction';
import { ActionTypes } from './actionTypes';
import { isCommValid } from './actionUtils';

export type MATLABStatus = {
  isMatlabLicensed: boolean;
  matlabStatus: string;
  matlabProxyHasError: boolean;
  licensingMode: string;
  matlabVersion: string;
  matlabRootPath: string;
  processStartTimeout: number;
};

export class MatlabStatusAction extends BaseAction {
    private static status: MATLABStatus;
    private static blockingPromise: PromiseDelegate<ReadonlyJSONValue> | null;

    constructor (blocking: boolean) {
        super();
        this.blocking = blocking;
    }

    public static getStatus (): MATLABStatus {
        return MatlabStatusAction.status;
    }

    public getActionName (): string {
        return ActionTypes.MATLAB_STATUS;
    }

    public async execute (data: any, comm: ICommunicationChannel): Promise<void> {
        if (!MatlabStatusAction.blockingPromise) {
            MatlabStatusAction.blockingPromise =
        new PromiseDelegate<ReadonlyJSONValue>();
        }

        console.debug('MatlabStatusAction execute called with data ', data);
        this.fetchMatlabStatus(comm);

        if (this.blocking) {
            console.debug(
                'This is a blocking action will wait for promise to resolve...'
            );
            await MatlabStatusAction.blockingPromise.promise;
        }
        console.debug('MatlabStatusAction execute completed');
    }

    public onMsg (data: any, _: ICommunicationChannel): void {
        console.debug('Received data for matlab_status action from kernel ', data);
        MatlabStatusAction.status = data.data as MATLABStatus;

        if (MatlabStatusAction.blockingPromise) {
            console.debug('Resolved blocking promise...');
            MatlabStatusAction.blockingPromise.resolve(null);
            MatlabStatusAction.blockingPromise = null;
        }

        console.debug('MatlabStatusAction onMsg completed');
    }

    private fetchMatlabStatus (comm: ICommunicationChannel): any {
        if (!isCommValid(comm)) {
            console.error('Communication channel is not available');
            return false;
        }

        comm.send({
            action: 'matlab_status',
            data: {}
        });
    }
}
