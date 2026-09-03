// Copyright 2026 The MathWorks, Inc.

import {
    openMatlabInNewTab,
    openAsLiveCodeInMatlabButtonHandler
} from '../../utils/commands';
import { Notification } from '@jupyterlab/apputils';

import { getFileNameForConversion } from '../../utils/file';
import {
    startMatlab,
    waitForMatlabToStart,
    convertToLiveCodeAndOpenMatlab,
    waitForUserToSignin
} from '../../utils/matlab';
import {
    displayUserSigninNotification
} from '../../utils/notifications';
import { showMatlabKernelIsBusyDialog } from '../../utils/dialogs';

// --------------------
// Mocks
// --------------------
jest.mock('../../utils/file', () => ({
    getFileNameForConversion: jest.fn()
}));
const mockedGetFileNameForConversion = getFileNameForConversion as jest.MockedFunction<typeof getFileNameForConversion>;

jest.mock('../../utils/matlab', () => ({
    startMatlab: jest.fn(),
    waitForMatlabToStart: jest.fn(),
    convertToLiveCodeAndOpenMatlab: jest.fn(),
    waitForUserToSignin: jest.fn()
}));
const mockedStartMatlab = startMatlab as jest.MockedFunction<typeof startMatlab>;
const mockedConvertToLiveCodeAndOpenMatlab = convertToLiveCodeAndOpenMatlab as jest.MockedFunction<typeof convertToLiveCodeAndOpenMatlab>;
const mockedWaitForMatlabToStart = waitForMatlabToStart as jest.MockedFunction<typeof waitForMatlabToStart>;
const mockedWaitForUserToSignin = waitForUserToSignin as jest.MockedFunction<typeof waitForUserToSignin>;

jest.mock('@jupyterlab/apputils', () => ({
    Notification: {
        info: jest.fn()
    }
}));

jest.mock('../../utils/notifications', () => ({
    displayUserSigninNotification: jest.fn()
}));
const mockedDisplayUserSigninNotification = displayUserSigninNotification as jest.MockedFunction<typeof displayUserSigninNotification>;

jest.mock('../../utils/dialogs', () => ({
    showMatlabKernelIsBusyDialog: jest.fn()
}));
const mockedShowMatlabKernelIsBusyDialog = showMatlabKernelIsBusyDialog as jest.MockedFunction<typeof showMatlabKernelIsBusyDialog>;

// ------------------------------
// Test Suite
// ------------------------------
describe('Commands module', () => {
    let panel: any;
    let commService: any;
    const targetURL = 'http://localhost:8888/matlab/kernel-123/';

    beforeEach(() => {
        jest.clearAllMocks();

        commService = {
            getComm: jest.fn().mockResolvedValue({})
        };

        // DEFAULT: MATLAB kernel, idle, not busy
        panel = {
            id: 'notebook-123',
            context: { path: 'abc.ipynb' },
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
    });

    it('openMatlabInNewTab opens MATLAB in new tab', async () => {
        const mockWindowOpen = jest.fn();
        (global as any).window = { open: mockWindowOpen };
        mockWindowOpen.mockReturnValue({});

        await openMatlabInNewTab(targetURL);

        expect(mockWindowOpen).toHaveBeenCalledTimes(1);
        expect(mockWindowOpen).toHaveBeenCalledWith(targetURL, '_blank');
    });

    it('calls busy dialog when NotebookInfo detects busy kernel', async () => {
        panel.sessionContext.session.kernel.status = 'busy';
        mockedGetFileNameForConversion.mockResolvedValue('file.mlx');
        mockedStartMatlab.mockResolvedValue({
            isMatlabLicensed: true,
            matlabStatus: 'up',
            matlabProxyHasError: false,
            licensingMode: 'online',
            matlabVersion: 'R2024a',
            matlabRootPath: '/usr/local/MATLAB'
        });

        await openAsLiveCodeInMatlabButtonHandler(panel, commService);

        expect(mockedShowMatlabKernelIsBusyDialog).toHaveBeenCalled();
    });

    it('returns early when getFileNameForConversion returns null', async () => {
        mockedGetFileNameForConversion.mockResolvedValue(null);

        await openAsLiveCodeInMatlabButtonHandler(panel, commService);

        expect(mockedStartMatlab).not.toHaveBeenCalled();
        expect(mockedConvertToLiveCodeAndOpenMatlab).not.toHaveBeenCalled();
        expect(Notification.info).not.toHaveBeenCalled();
    });

    it('handles MATLAB not licensed: signin flow + window open + conversion', async () => {
        panel.sessionContext.session.kernel.status = 'idle';
        mockedGetFileNameForConversion.mockResolvedValue('file.mlx');
        mockedStartMatlab.mockResolvedValue({
            isMatlabLicensed: false,
            matlabStatus: 'down',
            matlabProxyHasError: false,
            licensingMode: '',
            matlabVersion: '',
            matlabRootPath: ''
        });
        mockedDisplayUserSigninNotification.mockResolvedValue({} as any);
        mockedWaitForMatlabToStart.mockResolvedValue();
        mockedWaitForUserToSignin.mockResolvedValue();

        const mockWindowOpen = jest.fn();
        (global as any).window = { open: mockWindowOpen };
        mockWindowOpen.mockReturnValue({});

        await openAsLiveCodeInMatlabButtonHandler(panel, commService);

        expect(mockedDisplayUserSigninNotification).toHaveBeenCalled();
        expect(mockedWaitForUserToSignin).toHaveBeenCalled();
        expect(mockedWaitForMatlabToStart).toHaveBeenCalled();
        expect(mockedConvertToLiveCodeAndOpenMatlab).toHaveBeenCalled();
    });

    it('handles MATLAB licensed: waits + converts', async () => {
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
        mockedWaitForMatlabToStart.mockResolvedValue();

        const mockWindowOpen = jest.fn();
        (global as any).window = { open: mockWindowOpen };
        mockWindowOpen.mockReturnValue({});

        await openAsLiveCodeInMatlabButtonHandler(panel, commService);

        expect(mockedDisplayUserSigninNotification).not.toHaveBeenCalled();
        expect(mockedWaitForUserToSignin).not.toHaveBeenCalled();
        expect(mockedWaitForMatlabToStart).toHaveBeenCalled();
        expect(mockedConvertToLiveCodeAndOpenMatlab).toHaveBeenCalled();
    });
});
