// Copyright 2026 The MathWorks, Inc.

import { exportHandler } from '../../utils/export';
import {
    displayUserSigninNotification
} from '../../utils/notifications';
import { showMatlabKernelIsBusyDialog } from '../../utils/dialogs';
import {
    getFileNameForConversion
} from '../../utils/file';
import {
    convertToLiveCode,
    startMatlab,
    waitForMatlabToStart,
    waitForUserToSignin
} from '../../utils/matlab';
import { openMatlabInNewTab } from '../../utils/commands';
import { Notification } from '@jupyterlab/apputils';
import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';

// --------------------
// MOCKS
// --------------------

jest.mock('../../utils/notifications', () => ({
    displayUserSigninNotification: jest.fn()
}));
const mockedDisplayUserSigninNotification = displayUserSigninNotification as jest.MockedFunction<typeof displayUserSigninNotification>;

jest.mock('../../utils/dialogs', () => ({
    showMatlabKernelIsBusyDialog: jest.fn()
}));
const mockedShowMatlabKernelIsBusyDialog = showMatlabKernelIsBusyDialog as jest.MockedFunction<typeof showMatlabKernelIsBusyDialog>;

jest.mock('../../utils/file', () => ({
    getFileNameForConversion: jest.fn()
}));
const mockedGetFileNameForConversion = getFileNameForConversion as jest.MockedFunction<typeof getFileNameForConversion>;

jest.mock('../../utils/matlab', () => ({
    convertToLiveCode: jest.fn(),
    startMatlab: jest.fn(),
    waitForMatlabToStart: jest.fn(),
    waitForUserToSignin: jest.fn()
}));
const mockedStartMatlab = startMatlab as jest.MockedFunction<typeof startMatlab>;
const mockedConvertToLiveCode = convertToLiveCode as jest.MockedFunction<typeof convertToLiveCode>;
const mockedWaitForMatlabToStart = waitForMatlabToStart as jest.MockedFunction<typeof waitForMatlabToStart>;
const mockedWaitForUserToSignin = waitForUserToSignin as jest.MockedFunction<typeof waitForUserToSignin>;

jest.mock('../../utils/commands', () => ({
    openMatlabInNewTab: jest.fn()
}));
const mockedOpenMatlabInNewTab = openMatlabInNewTab as jest.MockedFunction<typeof openMatlabInNewTab>;

jest.mock('@jupyterlab/apputils', () => ({
    Notification: {
        info: jest.fn()
    }
}));

describe('exportHandler', () => {
    let commService: any;
    let panel: any;
    beforeEach(() => {
        jest.clearAllMocks();

        commService = {
            getComm: jest.fn().mockResolvedValue({}) // mock comm object
        };

        panel = {
            id: 'notebook-123',
            context: { path: 'abc.ipynb', save: jest.fn().mockResolvedValue(undefined) },
            sessionContext: {
                isReady: true,
                ready: Promise.resolve(),
                kernelDisplayName: 'MATLAB Kernel',
                session: {
                    kernel: {
                        id: 'kernel-123',
                        status: 'busy'
                    }
                }
            }
        };
    });

    it('logs error when panel is null and returns early', async () => {
        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => { });

        await exportHandler(commService, null);

        expect(errorSpy).toHaveBeenCalledWith('No active notebook to export');
        expect(commService.getComm).not.toHaveBeenCalled();

        errorSpy.mockRestore();
    });

    it('shows busy dialog when notebook is busy', async () => {
        mockedGetFileNameForConversion.mockResolvedValue('file.mlx');
        mockedStartMatlab.mockResolvedValue({
            isMatlabLicensed: true,
            matlabStatus: 'up',
            matlabProxyHasError: false,
            licensingMode: 'online',
            matlabVersion: 'R2024a',
            matlabRootPath: '/usr/local/MATLAB'
        });

        await exportHandler(commService, panel);

        expect(mockedShowMatlabKernelIsBusyDialog).toHaveBeenCalled();
    });

    it('returns early if getFileNameForConversion returns null', async () => {
        panel.sessionContext.session.kernel.status = 'idle';
        mockedGetFileNameForConversion.mockResolvedValue(null);

        await exportHandler(commService, panel);

        expect(mockedStartMatlab).not.toHaveBeenCalled();
        expect(mockedConvertToLiveCode).not.toHaveBeenCalled();
        expect(Notification.info).not.toHaveBeenCalled();
    });

    it('handles MATLAB not licensed flow and closes window after user sign in', async () => {
        panel.sessionContext.session.kernel.status = 'idle';
        const fakeWindow = { closed: false, close: jest.fn() } as unknown as Window;

        mockedStartMatlab.mockResolvedValue({
            isMatlabLicensed: false,
            matlabStatus: 'down',
            matlabProxyHasError: false,
            licensingMode: '',
            matlabVersion: '',
            matlabRootPath: ''
        });

        mockedDisplayUserSigninNotification.mockResolvedValue({
            promise: Promise.resolve({})
        } as PromiseDelegate<ReadonlyJSONValue>);

        mockedOpenMatlabInNewTab.mockResolvedValue(fakeWindow);

        mockedGetFileNameForConversion.mockResolvedValue('file.mlx');
        mockedWaitForMatlabToStart.mockResolvedValue(undefined);
        mockedWaitForUserToSignin.mockResolvedValue(undefined);

        await exportHandler(commService, panel);

        expect(openMatlabInNewTab).toHaveBeenCalled();
        expect(fakeWindow.close).toHaveBeenCalled();
    });

    it('executes full conversion flow when MATLAB is licensed', async () => {
        panel.sessionContext.session.kernel.status = 'idle';
        mockedGetFileNameForConversion.mockResolvedValue('file.mlx');
        mockedStartMatlab.mockResolvedValue({
            isMatlabLicensed: true,
            matlabStatus: 'up',
            matlabProxyHasError: false,
            licensingMode: 'online',
            matlabVersion: 'R2024a',
            matlabRootPath: '/usr/local/MATLAB'
        });
        mockedWaitForMatlabToStart.mockResolvedValue(undefined);

        await exportHandler(commService, panel);

        expect(startMatlab).toHaveBeenCalled();
        expect(waitForMatlabToStart).toHaveBeenCalled();
        expect(convertToLiveCode).toHaveBeenCalledWith(panel, expect.any(Object), expect.any(String), 'file.mlx');
        expect(Notification.info).toHaveBeenCalledWith('File file.mlx ready', { autoClose: 2000 });
    });
});
