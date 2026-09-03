// Copyright 2026 The MathWorks, Inc.

import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';

import { ICommunicationChannel } from '../matlabCommunication';
import { BaseAction } from './baseAction';
import { ActionTypes } from './actionTypes';
import { isCommValid } from './actionUtils';

export class StartMatlabProxyAction extends BaseAction {
    private static blockingPromise: PromiseDelegate<ReadonlyJSONValue> | null;

    constructor (blocking: boolean) {
        super();
        this.blocking = blocking;
    }

    public getActionName (): string {
        return ActionTypes.START_MATLAB_PROXY;
    }

    public async execute (data: any, comm: ICommunicationChannel): Promise<void> {
        if (!StartMatlabProxyAction.blockingPromise) {
            StartMatlabProxyAction.blockingPromise =
        new PromiseDelegate<ReadonlyJSONValue>();
        }

        console.debug('StartMatlab execute action called with data ', data);
        this.sendStartMatlabRequest(comm);

        if (this.blocking) {
            console.debug(
                'This is a blocking action will wait for promise to resolve...'
            );
            await StartMatlabProxyAction.blockingPromise.promise;
        }
    }

    public onMsg (data: any, _: ICommunicationChannel): void {
        if ('error' in data && data.error) {
            console.error('Received error from kernel ', data.error);
            if (StartMatlabProxyAction.blockingPromise) {
                StartMatlabProxyAction.blockingPromise.reject({ reason: data.error });
                StartMatlabProxyAction.blockingPromise = null;
            }
            return;
        }
        if (StartMatlabProxyAction.blockingPromise) {
            StartMatlabProxyAction.blockingPromise.resolve(null);
            StartMatlabProxyAction.blockingPromise = null;
        }

        console.debug('StartMatlab action onMsg completed');
    }

    private sendStartMatlabRequest (comm: ICommunicationChannel): void {
        if (!isCommValid(comm)) {
            console.error('Communication channel is not available');
            return;
        }

        comm.send({
            action: ActionTypes.START_MATLAB_PROXY,
            data: {}
        });
    }
}
