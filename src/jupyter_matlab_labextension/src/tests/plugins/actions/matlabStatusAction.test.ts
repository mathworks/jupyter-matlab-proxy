// Copyright 2026 The MathWorks, Inc.

import { MatlabStatusAction, MATLABStatus } from '../../../plugins/actions/matlabStatusAction';
import { ActionTypes } from '../../../plugins/actions/actionTypes';
import { ICommunicationChannel } from '../../../plugins/matlabCommunication';

describe('MatlabStatusAction', () => {
    let action: MatlabStatusAction;
    let mockComm: ICommunicationChannel;

    beforeEach(() => {
        jest.clearAllMocks();
        action = new MatlabStatusAction(false);
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
            const blockingAction = new MatlabStatusAction(true);
            expect(blockingAction.blocking).toBe(true);
        });

        it('should set blocking to false when passed false', () => {
            const nonBlockingAction = new MatlabStatusAction(false);
            expect(nonBlockingAction.blocking).toBe(false);
        });
    });

    describe('getActionName', () => {
        it('should return MATLAB_STATUS action type', () => {
            expect(action.getActionName()).toBe(ActionTypes.MATLAB_STATUS);
        });
    });

    describe('getStatus', () => {
        it('should return status after onMsg is called', () => {
            const mockStatus: MATLABStatus = {
                isMatlabLicensed: true,
                matlabStatus: 'up',
                matlabProxyHasError: false,
                licensingMode: 'online',
                matlabVersion: 'R2024a',
                matlabRootPath: '/usr/local/MATLAB'
            };

            action.onMsg({ data: mockStatus }, mockComm);

            expect(MatlabStatusAction.getStatus()).toEqual(mockStatus);
        });
    });

    describe('execute', () => {
        it('should send matlab_status request to comm', async () => {
            await action.execute(null, mockComm);

            expect(mockComm.send).toHaveBeenCalledWith({
                action: 'matlab_status',
                data: {}
            });
        });
    });

    describe('onMsg', () => {
        it('should update status from received data', () => {
            const mockStatus: MATLABStatus = {
                isMatlabLicensed: false,
                matlabStatus: 'starting',
                matlabProxyHasError: false,
                licensingMode: '',
                matlabVersion: '',
                matlabRootPath: ''
            };

            action.onMsg({ data: mockStatus }, mockComm);

            const status = MatlabStatusAction.getStatus();
            expect(status.isMatlabLicensed).toBe(false);
            expect(status.matlabStatus).toBe('starting');
        });

        it('should update status when MATLAB is up and licensed', () => {
            const mockStatus: MATLABStatus = {
                isMatlabLicensed: true,
                matlabStatus: 'up',
                matlabProxyHasError: false,
                licensingMode: 'online',
                matlabVersion: 'R2024a',
                matlabRootPath: '/usr/local/MATLAB/R2024a'
            };

            action.onMsg({ data: mockStatus }, mockComm);

            const status = MatlabStatusAction.getStatus();
            expect(status.isMatlabLicensed).toBe(true);
            expect(status.matlabStatus).toBe('up');
            expect(status.matlabVersion).toBe('R2024a');
        });
    });
});
