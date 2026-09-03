// Copyright 2026 The MathWorks, Inc.

import * as matlabModule from '../../utils/matlab';
import { PageConfig } from '@jupyterlab/coreutils';
import { ActionFactory } from '../../plugins/actions/actionFactory';
import { ActionTypes } from '../../plugins/actions/actionTypes';
import { MatlabStatusAction } from '../../plugins/actions/matlabStatusAction';
import { ConvertAction } from '../../plugins/actions/convertAction';
import {
    displayOpenMatlabNotification,
    displayStartingMatlabNotification
} from '../../utils/notifications';

const {
    getMatlabProxyStatus,
    startMatlab,
    waitForMatlabToStart,
    convertToLiveCodeAndOpenMatlab,
    openGeneratedFileInEditor,
    convertToLiveCode,
    waitForUserToSignin
} = matlabModule;

jest.mock('@jupyterlab/coreutils', () => ({
    PageConfig: {
        getBaseUrl: jest.fn(),
        getOption: jest.fn()
    }
}));

jest.mock('../../plugins/actions/actionFactory', () => ({
    ActionFactory: {
        createAction: jest.fn()
    }
}));

jest.mock('../../plugins/actions/matlabStatusAction', () => ({
    MatlabStatusAction: {
        getStatus: jest.fn()
    }
}));

jest.mock('../../plugins/actions/convertAction', () => ({
    ConvertAction: {
        getGeneratedLiveCodeFilePath: jest.fn()
    }
}));

jest.mock('../../utils/notifications', () => ({
    displayOpenMatlabNotification: jest.fn(),
    displayStartingMatlabNotification: jest.fn()
}));

const mockWindowOpen = jest.fn();
(global as any).window = { open: mockWindowOpen };

const mockedGetBaseUrl = PageConfig.getBaseUrl as jest.MockedFunction<typeof PageConfig.getBaseUrl>;
const mockedGetOption = PageConfig.getOption as jest.MockedFunction<typeof PageConfig.getOption>;
const mockedCreateAction = ActionFactory.createAction as jest.Mock;
const mockedMatlabStatusGet = MatlabStatusAction.getStatus as jest.Mock;
const mockedConvertGetPath = ConvertAction.getGeneratedLiveCodeFilePath as jest.MockedFunction<typeof ConvertAction.getGeneratedLiveCodeFilePath>;
const mockedDisplayOpenMatlab = displayOpenMatlabNotification as jest.MockedFunction<typeof displayOpenMatlabNotification>;
const mockedDisplayStarting = displayStartingMatlabNotification as jest.MockedFunction<typeof displayStartingMatlabNotification>;

describe('matlab utils', () => {
    let panel: any;
    let comm: any;

    beforeEach(() => {
        jest.clearAllMocks();

        panel = {
            context: {
                path: '/home/user/notebook.ipynb'
            },
            sessionContext: {
                isReady: true,
                ready: Promise.resolve(),
                kernelDisplayName: 'MATLAB Kernel',
                session: {
                    kernel: {
                        id: 'kernel-123',
                        status: 'idle'
                    }
                }
            }
        };

        comm = {};
    });

    // =========================================================
    // getMatlabProxyStatus
    // =========================================================
    it('getMatlabProxyStatus executes MATLAB_STATUS action and returns status', async () => {
        const actionInstance = { execute: jest.fn().mockResolvedValue(undefined) };
        const fakeStatus = { matlab: { status: 'up' }, isLicensed: true };

        mockedCreateAction.mockReturnValue(actionInstance);
        mockedMatlabStatusGet.mockReturnValue(fakeStatus);

        const result = await getMatlabProxyStatus(panel, comm);

        expect(mockedCreateAction).toHaveBeenCalledWith(
            ActionTypes.MATLAB_STATUS,
            true
        );
        expect(actionInstance.execute).toHaveBeenCalledWith(null, comm);
        expect(result).toBe(fakeStatus);
    });

    // =========================================================
    // startMatlab
    // =========================================================
    it('startMatlab sends START_MATLAB_PROXY and then gets status', async () => {
        const startAction = { execute: jest.fn().mockResolvedValue(undefined) };
        const statusAction = { execute: jest.fn().mockResolvedValue(undefined) };

        // First call returns startAction, second call returns statusAction (for getMatlabProxyStatus)
        mockedCreateAction
            .mockReturnValueOnce(startAction)
            .mockReturnValueOnce(statusAction);

        const fakeStatus = {
            isMatlabLicensed: true,
            matlabStatus: 'up',
            matlabProxyHasError: false,
            licensingMode: 'online',
            matlabVersion: 'R2024a',
            matlabRootPath: '/usr/local/MATLAB'
        };
        mockedMatlabStatusGet.mockReturnValue(fakeStatus);

        const result = await startMatlab(panel, comm);

        expect(mockedCreateAction).toHaveBeenCalledWith(
            ActionTypes.START_MATLAB_PROXY,
            true
        );
        expect(startAction.execute).toHaveBeenCalledWith(null, comm);
        expect(result).toEqual(fakeStatus);
    });

    // =========================================================
    // waitForMatlabToStart
    // =========================================================
    it('waitForMatlabToStart resolves when matlab status becomes up', async () => {
        const statusAction = { execute: jest.fn().mockResolvedValue(undefined) };
        mockedCreateAction.mockReturnValue(statusAction);

        // First call: not up, Second call: up (using matlabStatus not matlab.status)
        mockedMatlabStatusGet
            .mockReturnValueOnce({ matlabStatus: 'starting', processStartTimeout: 600 } as any)
            .mockReturnValueOnce({ matlabStatus: 'up', processStartTimeout: 600 } as any);

        const notificationDelegate = {
            resolve: jest.fn(),
            reject: jest.fn()
        } as any;

        mockedDisplayStarting.mockReturnValue(notificationDelegate);

        await waitForMatlabToStart(1, comm, panel);

        expect(statusAction.execute).toHaveBeenCalledTimes(2);
        expect(notificationDelegate.resolve).toHaveBeenCalled();
        expect(notificationDelegate.reject).not.toHaveBeenCalled();
    });

    it('waitForMatlabToStart rejects when timeout reached', async () => {
        const statusAction = { execute: jest.fn().mockResolvedValue(undefined) };
        mockedCreateAction.mockReturnValue(statusAction);

        // MATLAB never up. Tiny process start timeout (0.005s -> 5ms) so the test
        // doesn't hang while still exercising the timeout-rejection path.
        mockedMatlabStatusGet.mockReturnValue({ matlabStatus: 'starting', processStartTimeout: 0.005 } as any);

        const notificationDelegate = {
            resolve: jest.fn(),
            reject: jest.fn()
        } as any;

        mockedDisplayStarting.mockReturnValue(notificationDelegate);

        await waitForMatlabToStart(1, comm, panel);

        expect(notificationDelegate.reject).toHaveBeenCalled();
    });

    // =========================================================
    // convertToLiveCode
    // =========================================================
    it('convertToLiveCode executes CONVERT action and returns generated file path', async () => {
        const convertActionInstance = { execute: jest.fn().mockResolvedValue(undefined) };
        mockedCreateAction.mockReturnValue(convertActionInstance);
        mockedConvertGetPath.mockReturnValue('/home/user/notebook.mlx');

        const result = await convertToLiveCode(panel, comm, '/home/user/notebook.ipynb', '/home/user/notebook.mlx');

        expect(mockedCreateAction).toHaveBeenCalledWith(
            ActionTypes.CONVERT,
            true
        );
        expect(convertActionInstance.execute).toHaveBeenCalledWith(
            {
                ipynbFilePath: '/home/user/notebook.ipynb',
                liveCodeFilePath: '/home/user/notebook.mlx'
            },
            comm
        );
        expect(result).toBe('/home/user/notebook.mlx');
    });

    // =========================================================
    // openGeneratedFileInEditor
    // =========================================================
    it('openGeneratedFileInEditor executes EDIT action with proper payload', async () => {
        const editAction = { execute: jest.fn().mockResolvedValue(undefined) };
        mockedCreateAction.mockReturnValue(editAction);

        await openGeneratedFileInEditor(panel, comm, '/home/user/notebook.mlx');

        expect(mockedCreateAction).toHaveBeenCalledWith(
            ActionTypes.EDIT,
            true
        );
        expect(editAction.execute).toHaveBeenCalledWith(
            {
                action: ActionTypes.EDIT,
                liveCodeFilePath: '/home/user/notebook.mlx'
            },
            comm
        );
    });

    // =========================================================
    // convertToLiveCodeAndOpenMatlab
    // =========================================================
    describe('convertToLiveCodeAndOpenMatlab', () => {
        beforeEach(() => {
            jest.useFakeTimers();
            mockedGetBaseUrl.mockReturnValue('http://localhost:8888/');
            mockedGetOption.mockReturnValue('/home/user');
            mockWindowOpen.mockReturnValue({ closed: false });
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        it('opens MATLAB and editor when generated file path is returned and shouldOpenMatlab=true', async () => {
            // Mock the CONVERT action for convertToLiveCode
            const convertAction = { execute: jest.fn().mockResolvedValue(undefined) };
            // Mock the EDIT action for openGeneratedFileInEditor
            const editAction = { execute: jest.fn().mockResolvedValue(undefined) };

            mockedCreateAction
                .mockReturnValueOnce(convertAction)
                .mockReturnValueOnce(editAction);

            mockedConvertGetPath.mockReturnValue('/home/user/notebook.mlx');

            const promise = convertToLiveCodeAndOpenMatlab(
                panel,
                comm,
                '/home/user/notebook.mlx',
                true
            );

            // Run all pending timers and promises
            await jest.runAllTimersAsync();
            await promise;

            expect(mockedCreateAction).toHaveBeenCalledWith(ActionTypes.CONVERT, true);
            expect(mockedDisplayOpenMatlab).toHaveBeenCalled();
            expect(editAction.execute).toHaveBeenCalled();
            expect(mockWindowOpen).toHaveBeenCalledWith(
                'http://localhost:8888/matlab/kernel-123/',
                '_blank'
            );
        });

        it('does not open MATLAB when shouldOpenMatlab=false', async () => {
            const convertAction = { execute: jest.fn().mockResolvedValue(undefined) };
            const editAction = { execute: jest.fn().mockResolvedValue(undefined) };

            mockedCreateAction
                .mockReturnValueOnce(convertAction)
                .mockReturnValueOnce(editAction);

            mockedConvertGetPath.mockReturnValue('/home/user/notebook.mlx');

            await convertToLiveCodeAndOpenMatlab(
                panel,
                comm,
                '/home/user/notebook.mlx',
                false
            );

            expect(convertAction.execute).toHaveBeenCalled();
            expect(mockedDisplayOpenMatlab).not.toHaveBeenCalled();
            jest.runAllTimers();
            expect(mockWindowOpen).not.toHaveBeenCalled();
            expect(editAction.execute).toHaveBeenCalled();
        });

        it('does nothing when convertToLiveCode returns falsy', async () => {
            const convertAction = { execute: jest.fn().mockResolvedValue(undefined) };

            mockedCreateAction.mockReturnValueOnce(convertAction);
            mockedConvertGetPath.mockReturnValue('');
            const openEditorSpy = jest
                .spyOn(matlabModule, 'openGeneratedFileInEditor')
                .mockResolvedValue(undefined as any);

            await convertToLiveCodeAndOpenMatlab(
                panel,
                comm,
                '/home/user/notebook.mlx',
                true
            );

            expect(convertAction.execute).toHaveBeenCalled();
            expect(mockedDisplayOpenMatlab).not.toHaveBeenCalled();
            jest.runAllTimers();
            expect(mockWindowOpen).not.toHaveBeenCalled();
            expect(openEditorSpy).not.toHaveBeenCalled();
        });
    });

    // =========================================================
    // waitForUserToSignin
    // =========================================================
    it('waitForUserToSignin resolves when isMatlabLicensed becomes true', async () => {
        const statusAction = { execute: jest.fn().mockResolvedValue(undefined) };
        mockedCreateAction.mockReturnValue(statusAction);

        mockedMatlabStatusGet
            .mockReturnValueOnce({ isMatlabLicensed: false } as any)
            .mockReturnValueOnce({ isMatlabLicensed: true } as any);

        const delegate: any = {
            resolve: jest.fn(),
            reject: jest.fn()
        };

        await waitForUserToSignin(1, comm, delegate as any, 100);

        expect(statusAction.execute).toHaveBeenCalledTimes(2);
        expect(delegate.resolve).toHaveBeenCalled();
        expect(delegate.reject).not.toHaveBeenCalled();
    });

    it('waitForUserToSignin rejects when timeout reached', async () => {
        const statusAction = { execute: jest.fn().mockResolvedValue(undefined) };
        mockedCreateAction.mockReturnValue(statusAction);

        mockedMatlabStatusGet.mockReturnValue({ isMatlabLicensed: false } as any);

        const delegate: any = {
            resolve: jest.fn(),
            reject: jest.fn()
        };

        await waitForUserToSignin(1, comm, delegate as any, 5);

        expect(delegate.reject).toHaveBeenCalled();
    });
});
