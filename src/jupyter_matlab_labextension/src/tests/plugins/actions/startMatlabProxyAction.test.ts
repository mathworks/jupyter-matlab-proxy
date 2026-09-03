// Copyright 2026 The MathWorks, Inc.

import { StartMatlabProxyAction } from '../../../plugins/actions/startMatlabProxyAction';
import { ActionTypes } from '../../../plugins/actions/actionTypes';
import { ICommunicationChannel } from '../../../plugins/matlabCommunication';

describe('StartMatlabProxyAction', () => {
    let action: StartMatlabProxyAction;
    let mockComm: ICommunicationChannel;

    beforeEach(() => {
        jest.clearAllMocks();
        action = new StartMatlabProxyAction(false);
        mockComm = {
            commId: 'test-comm-id',
            targetName: 'matlab',
            isDisposed: false,
            send: jest.fn(),
            close: jest.fn(),
            open: jest.fn(),
            onMsg: null,
            onClose: null
        } as unknown as ICommunicationChannel;
    });

    describe('constructor', () => {
        it('should set blocking to true when passed true', () => {
            const blockingAction = new StartMatlabProxyAction(true);
            expect(blockingAction.blocking).toBe(true);
        });

        it('should set blocking to false when passed false', () => {
            const nonBlockingAction = new StartMatlabProxyAction(false);
            expect(nonBlockingAction.blocking).toBe(false);
        });
    });

    describe('getActionName', () => {
        it('should return START_MATLAB_PROXY action type', () => {
            expect(action.getActionName()).toBe(ActionTypes.START_MATLAB_PROXY);
        });
    });

    describe('execute', () => {
        it('should send start_matlab_proxy request to comm', async () => {
            await action.execute(null, mockComm);

            expect(mockComm.send).toHaveBeenCalledWith({
                action: ActionTypes.START_MATLAB_PROXY,
                data: {}
            });
        });
    });

    describe('onMsg', () => {
        it('should complete successfully when no error in data', () => {
            const debugSpy = jest.spyOn(console, 'debug').mockImplementation();

            action.onMsg({}, mockComm);

            expect(debugSpy).toHaveBeenCalledWith('StartMatlab action onMsg completed');

            debugSpy.mockRestore();
        });

        it('should log error when error is present in data', () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            action.onMsg({ error: 'Failed to start MATLAB proxy' }, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('Received error from kernel ', 'Failed to start MATLAB proxy');

            errorSpy.mockRestore();
        });
    });
});
