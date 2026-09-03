// Copyright 2026 The MathWorks, Inc.

import { getFileNameForConversion } from '../../utils/file';
import { showDialog, InputDialog, Dialog } from '@jupyterlab/apputils';
import { ActionFactory } from '../../plugins/actions/actionFactory';
import { CheckFileExistsAction } from '../../plugins/actions/checkFileExistsAction';

jest.mock('@jupyterlab/apputils', () => ({
    showDialog: jest.fn(),
    InputDialog: { getText: jest.fn() },
    Dialog: {
        cancelButton: jest.fn(() => ({ label: 'Cancel' })),
        okButton: jest.fn(({ label } = { label: 'OK' }) => ({ label }))
    }
}));

jest.mock('@jupyterlab/coreutils', () => ({
    PathExt: {
        dirname: jest.fn((p) => p.split('/').slice(0, -1).join('/')),
        basename: jest.fn((p, ext) => {
            if (ext && p.endsWith(ext)) return p.slice(0, -ext.length);
            return p.split('/').pop();
        }),
        extname: jest.fn((p) => {
            const idx = p.lastIndexOf('.');
            return idx > -1 ? p.slice(idx) : '';
        }),
        join: jest.fn((a, b) => `${a}/${b}`)
    },
    PageConfig: {
        getOption: jest.fn().mockReturnValue('/home/user'),
        getBaseUrl: jest.fn().mockReturnValue('http://localhost:8888/')
    }
}));

jest.mock('../../plugins/actions/actionFactory', () => ({
    ActionFactory: {
        createAction: jest.fn()
    }
}));

jest.mock('../../plugins/actions/checkFileExistsAction', () => ({
    CheckFileExistsAction: {
        getFileExistsStatus: jest.fn()
    }
}));

const mockedShowDialog = showDialog as jest.MockedFunction<typeof showDialog>;
const mockedInput = InputDialog.getText as jest.MockedFunction<typeof InputDialog.getText>;
const mockedCreateAction = ActionFactory.createAction as jest.MockedFunction<typeof ActionFactory.createAction>;
const mockedFileStatus = CheckFileExistsAction.getFileExistsStatus as jest.MockedFunction<typeof CheckFileExistsAction.getFileExistsStatus>;

describe('getFileNameForConversion', () => {
    let panel: any;
    let comm: any;
    let fakeAction: any;

    beforeEach(() => {
        jest.clearAllMocks();

        panel = {
            context: {
                path: 'notebook.ipynb'
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

        fakeAction = {
            execute: jest.fn().mockResolvedValue(undefined)
        };

        mockedCreateAction.mockReturnValue(fakeAction);
    });

    it('returns default mlx filename when file does not exist', async () => {
        mockedFileStatus.mockReturnValue(false); // file does NOT exist

        const result = await getFileNameForConversion(panel, comm);

        expect(result).toBe('/home/user/notebook.mlx');

        expect(fakeAction.execute).toHaveBeenCalledWith(
            { ipynbFilePath: '/home/user/notebook.ipynb' },
            comm
        );
    });

    it('returns null when user cancels instead of replacing or renaming', async () => {
        mockedFileStatus.mockReturnValue(true);
        mockedShowDialog.mockResolvedValue({
            button: { label: 'Cancel', accept: false } as Dialog.IButton,
            value: null,
            isChecked: false
        } as Dialog.IResult<unknown>);

        const result = await getFileNameForConversion(panel, comm);

        expect(result).toBeNull();
    });

    it('returns default path when user chooses Replace button', async () => {
        mockedFileStatus.mockReturnValue(true);

        mockedShowDialog.mockResolvedValue({
            button: { label: 'Replace' } as Dialog.IButton,
            value: null,
            isChecked: false
        } as Dialog.IResult<unknown>);

        const result = await getFileNameForConversion(panel, comm);
        expect(result).toBe('/home/user/notebook.mlx');
    });

    it('returns new filename when user enters a new name', async () => {
        mockedFileStatus.mockReturnValue(true);

        // First dialog → choose "New Name"
        mockedShowDialog.mockResolvedValueOnce({
            button: { label: 'New Name' } as Dialog.IButton,
            value: null,
            isChecked: false
        } as Dialog.IResult<unknown>);

        mockedInput.mockResolvedValue({
            button: { accept: true } as Dialog.IButton,
            value: 'renamed_notebook',
            isChecked: false
        } as Dialog.IResult<string>);

        const result = await getFileNameForConversion(panel, comm);
        expect(result).toBe('/home/user/renamed_notebook.mlx');
    });

    it('returns null when user cancels name input dialog', async () => {
        mockedFileStatus.mockReturnValue(true);

        mockedShowDialog.mockResolvedValueOnce({
            button: { label: 'New Name' } as Dialog.IButton,
            value: null,
            isChecked: false
        } as Dialog.IResult<unknown>);

        mockedInput.mockResolvedValue({
            button: { accept: false },
            value: '',
            isChecked: false
        } as Dialog.IResult<string>);

        const result = await getFileNameForConversion(panel, comm);

        expect(result).toBeNull();
    });
});
