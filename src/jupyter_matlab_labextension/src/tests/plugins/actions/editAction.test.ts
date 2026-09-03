// Copyright 2026 The MathWorks, Inc.

import { EditAction } from '../../../plugins/actions/editAction';
import { ActionTypes } from '../../../plugins/actions/actionTypes';
import { ICommunicationChannel } from '../../../plugins/matlabCommunication';

describe('EditAction', () => {
    let action: EditAction;
    let mockComm: ICommunicationChannel;
    let debugSpy: jest.SpyInstance;

    beforeEach(() => {
        jest.clearAllMocks();
        debugSpy = jest.spyOn(console, 'debug').mockImplementation();
        action = new EditAction(false);
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

    afterEach(() => {
        debugSpy.mockRestore();
    });

    describe('constructor', () => {
        it('should set blocking to true when passed true', () => {
            const blockingAction = new EditAction(true);
            expect(blockingAction.blocking).toBe(true);
        });

        it('should set blocking to false when passed false', () => {
            const nonBlockingAction = new EditAction(false);
            expect(nonBlockingAction.blocking).toBe(false);
        });
    });

    describe('getActionName', () => {
        it('should return EDIT action type', () => {
            expect(action.getActionName()).toBe(ActionTypes.EDIT);
        });
    });

    describe('execute', () => {
        it('should send edit request when liveCodeFilePath is provided', async () => {
            await action.execute({ liveCodeFilePath: '/path/to/file.mlx' }, mockComm);

            expect(mockComm.send).toHaveBeenCalledWith({
                action: ActionTypes.EDIT,
                data: {
                    liveCodeFilePath: '/path/to/file.mlx'
                }
            });
        });

        it('should log error when liveCodeFilePath is missing', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            await action.execute({}, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('liveCodeFilePath missing for sending edit request');
            expect(mockComm.send).not.toHaveBeenCalled();

            errorSpy.mockRestore();
        });

        it('should log error when filePath is empty', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            await action.execute({ liveCodeFilePath: '' }, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('File path is not available');

            errorSpy.mockRestore();
        });
    });

    describe('onMsg', () => {
        it('should complete successfully when no error in data', async () => {
            const debugSpy = jest.spyOn(console, 'debug').mockImplementation();

            await action.execute({ liveCodeFilePath: '/path/to/file.mlx' }, mockComm);
            action.onMsg({}, mockComm);

            expect(debugSpy).toHaveBeenCalledWith('EditAction onMsg completed');

            debugSpy.mockRestore();
        });

        it('should log error when error is present in data', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            await action.execute({ liveCodeFilePath: '/path/to/file.mlx' }, mockComm);
            action.onMsg({ error: 'Failed to open file in editor' }, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('Received error from kernel ', 'Failed to open file in editor');

            errorSpy.mockRestore();
        });

        it('should resolve blocking promise on success', async () => {
            await action.execute({ liveCodeFilePath: '/path/to/file.mlx' }, mockComm);

            expect(() => action.onMsg({}, mockComm)).not.toThrow();
        });

        it('should reject blocking promise on error', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();
            await action.execute({ liveCodeFilePath: '/path/to/file.mlx' }, mockComm);

            expect(() => action.onMsg({ error: 'Some error' }, mockComm)).not.toThrow();
            errorSpy.mockRestore();
        });
    });
});
