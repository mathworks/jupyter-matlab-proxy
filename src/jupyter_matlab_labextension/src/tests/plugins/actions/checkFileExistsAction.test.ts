// Copyright 2026 The MathWorks, Inc.

import { CheckFileExistsAction } from '../../../plugins/actions/checkFileExistsAction';
import { ActionTypes } from '../../../plugins/actions/actionTypes';
import { ICommunicationChannel } from '../../../plugins/matlabCommunication';

describe('CheckFileExistsAction', () => {
    let action: CheckFileExistsAction;
    let mockComm: ICommunicationChannel;

    beforeEach(() => {
        jest.clearAllMocks();
        action = new CheckFileExistsAction(false);
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
            const blockingAction = new CheckFileExistsAction(true);
            expect(blockingAction.blocking).toBe(true);
        });

        it('should set blocking to false when passed false', () => {
            const nonBlockingAction = new CheckFileExistsAction(false);
            expect(nonBlockingAction.blocking).toBe(false);
        });
    });

    describe('getActionName', () => {
        it('should return CHECK_FILE_EXISTS action type', () => {
            expect(action.getActionName()).toBe(ActionTypes.CHECK_FILE_EXISTS);
        });
    });

    describe('getFileExistsStatus', () => {
        it('should return file exists status after onMsg is called', () => {
            action.onMsg({ exists: true }, mockComm);
            expect(CheckFileExistsAction.getFileExistsStatus()).toBe(true);

            action.onMsg({ exists: false }, mockComm);
            expect(CheckFileExistsAction.getFileExistsStatus()).toBe(false);
        });
    });

    describe('execute', () => {
        it('should log error when ipynbFilePath is missing', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            await action.execute({}, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('Missing data for executing CheckFileExists action...');
            expect(mockComm.send).not.toHaveBeenCalled();

            errorSpy.mockRestore();
        });

        it('should send check file exists request when ipynbFilePath is provided', async () => {
            await action.execute({ ipynbFilePath: '/path/to/file.ipynb' }, mockComm);

            expect(mockComm.send).toHaveBeenCalledWith({
                action: ActionTypes.CHECK_FILE_EXISTS,
                data: {
                    ipynbFilePath: '/path/to/file.ipynb'
                }
            });
        });

        it('should log error when filePath is empty', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            await action.execute({ ipynbFilePath: '' }, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('File path is not available');

            errorSpy.mockRestore();
        });
    });

    describe('onMsg', () => {
        it('should set fileExists to true when data.exists is true', () => {
            action.onMsg({ exists: true }, mockComm);

            expect(CheckFileExistsAction.getFileExistsStatus()).toBe(true);
        });

        it('should set fileExists to false when data.exists is false', () => {
            action.onMsg({ exists: false }, mockComm);

            expect(CheckFileExistsAction.getFileExistsStatus()).toBe(false);
        });

        it('should log error when error is present in data', () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            action.onMsg({ error: 'Some error occurred' }, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('Received error from kernel ', 'Some error occurred');

            errorSpy.mockRestore();
        });
    });
});
