// Copyright 2026 The MathWorks, Inc.

import { ConvertAction } from '../../../plugins/actions/convertAction';
import { ActionTypes } from '../../../plugins/actions/actionTypes';
import { ICommunicationChannel } from '../../../plugins/matlabCommunication';
import { displayConversionNotification, displayUnsupportedMatlabVersionNotification } from '../../../utils/notifications';
import { PromiseDelegate } from '@lumino/coreutils';

import { isCommValid } from '../../../plugins/actions/actionUtils';

jest.mock('../../../utils/notifications', () => ({
    displayConversionNotification: jest.fn(),
    displayUnsupportedMatlabVersionNotification: jest.fn()
}));

jest.mock('../../../plugins/actions/actionUtils', () => ({
    isCommValid: jest.fn()
}));

const mockedDisplayConversionNotification = displayConversionNotification as jest.MockedFunction<typeof displayConversionNotification>;
const mockedDisplayUnsupportedMatlabVersionNotification = displayUnsupportedMatlabVersionNotification as jest.MockedFunction<typeof displayUnsupportedMatlabVersionNotification>;
const mockedIsCommValid = isCommValid as jest.MockedFunction<typeof isCommValid>;

describe('ConvertAction', () => {
    let action: ConvertAction;
    let mockComm: ICommunicationChannel;

    beforeEach(() => {
        jest.clearAllMocks();
        action = new ConvertAction(false);
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
        mockedIsCommValid.mockReturnValue(true);
    });

    describe('constructor', () => {
        it('should create a blocking action when passed true', () => {
            const blockingAction = new ConvertAction(true);
            expect(blockingAction).toBeInstanceOf(ConvertAction);
        });

        it('should create a non-blocking action when passed false', () => {
            const nonBlockingAction = new ConvertAction(false);
            expect(nonBlockingAction).toBeInstanceOf(ConvertAction);
        });
    });

    describe('getActionName', () => {
        it('should return CONVERT action type', () => {
            expect(action.getActionName()).toBe(ActionTypes.CONVERT);
        });
    });

    describe('getGeneratedLiveCodeFilePath', () => {
        it('should return liveCodeFilePath after onMsg is called with valid data', () => {
            action.onMsg({ liveCodeFilePath: '/path/to/file.m' }, mockComm);

            expect(ConvertAction.getGeneratedLiveCodeFilePath()).toBe('/path/to/file.m');
        });
    });

    describe('execute', () => {
        it('should return early when comm is invalid', async () => {
            mockedIsCommValid.mockReturnValue(false);
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            await action.execute({}, mockComm);

            expect(mockComm.send).not.toHaveBeenCalled();
            expect(mockedDisplayConversionNotification).not.toHaveBeenCalled();

            errorSpy.mockRestore();
        });

        it('should call displayConversionNotification with correct parameters', async () => {
            const mockPromiseDelegate = {
                promise: Promise.resolve(),
                resolve: jest.fn(),
                reject: jest.fn()
            } as unknown as PromiseDelegate<any>;

            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);

            const data = { ipynbFilePath: '/path/to/notebook.ipynb', liveCodeFilePath: '/path/to/file.m' };
            await action.execute(data, mockComm);

            expect(mockedDisplayConversionNotification).toHaveBeenCalledWith(50000);
        });

        it('should wait for promise when blocking is true', async () => {
            const blockingAction = new ConvertAction(true);
            let promiseResolved = false;

            const mockPromiseDelegate = {
                promise: new Promise<void>((resolve) => {
                    setTimeout(() => {
                        promiseResolved = true;
                        resolve();
                    }, 10);
                }),
                resolve: jest.fn(),
                reject: jest.fn()
            } as unknown as PromiseDelegate<any>;

            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);

            await blockingAction.execute({}, mockComm);

            expect(promiseResolved).toBe(true);
        });
    });

    describe('onMsg', () => {
        beforeEach(() => {
            const mockPromiseDelegate = {
                promise: Promise.resolve(),
                resolve: jest.fn(),
                reject: jest.fn()
            } as unknown as PromiseDelegate<any>;
            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);
        });

        it('should update liveCodeFilePath when valid data is received', async () => {
            await action.execute({}, mockComm);

            action.onMsg({ liveCodeFilePath: '/path/to/generated.m' }, mockComm);

            expect(ConvertAction.getGeneratedLiveCodeFilePath()).toBe('/path/to/generated.m');
        });

        it('should display unsupported version notification for MATLABVersionUnsupportedForConversionError', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            const mockPromiseDelegate = {
                promise: Promise.resolve(),
                resolve: jest.fn(),
                reject: jest.fn()
            } as unknown as PromiseDelegate<any>;
            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);

            await action.execute({}, mockComm);
            action.onMsg({ error: 'MATLABVersionUnsupportedForConversionError: requires R2025a' }, mockComm);

            expect(mockedDisplayUnsupportedMatlabVersionNotification).toHaveBeenCalled();

            errorSpy.mockRestore();
        });

        it('should not display unsupported version notification for other errors', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            const mockPromiseDelegate = {
                promise: Promise.resolve(),
                resolve: jest.fn(),
                reject: jest.fn()
            } as unknown as PromiseDelegate<any>;
            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);

            await action.execute({}, mockComm);
            action.onMsg({ error: 'Some other error' }, mockComm);

            expect(mockedDisplayUnsupportedMatlabVersionNotification).not.toHaveBeenCalled();

            errorSpy.mockRestore();
        });

        it('should log error when error is present in data', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            const mockPromiseDelegate = {
                promise: Promise.resolve(),
                resolve: jest.fn(),
                reject: jest.fn()
            } as unknown as PromiseDelegate<any>;
            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);

            await action.execute({}, mockComm);
            action.onMsg({ error: 'Conversion failed' }, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('Received error from kernel ', 'Conversion failed');

            errorSpy.mockRestore();
        });

        it('should log error when liveCodeFilePath is missing in data', async () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            const mockPromiseDelegate = {
                promise: Promise.resolve(),
                resolve: jest.fn(),
                reject: jest.fn()
            } as unknown as PromiseDelegate<any>;
            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);

            await action.execute({}, mockComm);
            action.onMsg({}, mockComm);

            expect(errorSpy).toHaveBeenCalledWith('Did not receive liveCodeFilePath in data from kernel');

            errorSpy.mockRestore();
        });

        it('should resolve blocking promise when liveCodeFilePath is received', async () => {
            const resolveFn = jest.fn();
            const mockPromiseDelegate = {
                promise: Promise.resolve(),
                resolve: resolveFn,
                reject: jest.fn()
            } as unknown as PromiseDelegate<any>;
            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);

            await action.execute({}, mockComm);
            action.onMsg({ liveCodeFilePath: '/path/to/file.m' }, mockComm);

            expect(resolveFn).toHaveBeenCalledWith(null);
        });

        it('should reject blocking promise when error is received', async () => {
            const rejectFn = jest.fn();
            const mockPromiseDelegate = {
                promise: Promise.resolve(),
                resolve: jest.fn(),
                reject: rejectFn
            } as unknown as PromiseDelegate<any>;
            mockedDisplayConversionNotification.mockReturnValue(mockPromiseDelegate);

            await action.execute({}, mockComm);
            action.onMsg({ error: 'Some error' }, mockComm);

            expect(rejectFn).toHaveBeenCalled();
        });
    });
});
