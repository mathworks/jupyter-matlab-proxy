// Copyright 2026 The MathWorks, Inc.

import {
    getNewFileNameDialog,
    showMatlabKernelIsBusyDialog,
    showPopupBlockedDialog
} from '../../utils/dialogs';
import { showDialog, InputDialog, Dialog } from '@jupyterlab/apputils';

// --------------------
// Mocks
// --------------------
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
        basename: jest.fn((p, ext) => {
            if (ext && p.endsWith(ext)) return p.slice(0, -ext.length);
            return p.split('/').pop();
        }),
        extname: jest.fn((p) => {
            const idx = p.lastIndexOf('.');
            return idx > -1 ? p.slice(idx) : '';
        })
    }
}));

const mockedShowDialog = showDialog as jest.MockedFunction<typeof showDialog>;
const mockedInputGetText = InputDialog.getText as jest.MockedFunction<typeof InputDialog.getText>;

// ------------------------------
// Test Suite
// ------------------------------
describe('dialogs module', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('getNewFileNameDialog()', () => {
        it('returns null when user cancels the dialog', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'Cancel', accept: false } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            const result = await getNewFileNameDialog('notebook.ipynb');

            expect(result).toBeNull();
            expect(mockedShowDialog).toHaveBeenCalledWith({
                title: '"notebook" Live Script file already exists.',
                body: 'A file named "notebook" Live Script already exists in the folder. Choose a new name or replace it to overwrite its current contents',
                buttons: expect.any(Array)
            });
        });

        it('returns mlx filename when user chooses Replace', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'Replace', accept: true } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            const result = await getNewFileNameDialog('notebook.ipynb');

            expect(result).toBe('notebook.mlx');
        });

        it('prompts for new name when user chooses New Name and returns new filename', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'New Name', accept: true } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            mockedInputGetText.mockResolvedValue({
                button: { accept: true } as Dialog.IButton,
                value: 'renamed_notebook',
                isChecked: false
            } as Dialog.IResult<string>);

            const result = await getNewFileNameDialog('notebook.ipynb');

            expect(mockedInputGetText).toHaveBeenCalledWith({
                title: 'New File Name',
                label: 'Choose a new name for the file. Do not include a file extension',
                placeholder: 'Enter file name'
            });
            expect(result).toBe('renamed_notebook.mlx');
        });

        it('returns null when user chooses New Name but cancels the input dialog', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'New Name', accept: true } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            mockedInputGetText.mockResolvedValue({
                button: { accept: false } as Dialog.IButton,
                value: '',
                isChecked: false
            } as Dialog.IResult<string>);

            const result = await getNewFileNameDialog('notebook.ipynb');

            expect(result).toBeNull();
        });

        it('returns null when user chooses New Name but provides empty value', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'New Name', accept: true } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            mockedInputGetText.mockResolvedValue({
                button: { accept: true } as Dialog.IButton,
                value: '',
                isChecked: false
            } as Dialog.IResult<string>);

            const result = await getNewFileNameDialog('notebook.ipynb');

            expect(result).toBeNull();
        });
    });

    describe('showMatlabKernelIsBusyDialog', () => {
        it('displays kernel busy dialog with correct title and body', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'OK', accept: true } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            await showMatlabKernelIsBusyDialog();

            expect(mockedShowDialog).toHaveBeenCalledWith({
                title: 'MATLAB Kernel Busy',
                body: 'The MATLAB kernel must be idle to open the Notebook as Live Script in MATLAB. Try again when the MATLAB kernel is idle.',
                buttons: expect.any(Array)
            });
        });

        it('resolves after user clicks OK', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'OK', accept: true } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            await expect(showMatlabKernelIsBusyDialog()).resolves.toBeUndefined();
        });
    });

    describe('showPopupBlockedDialog', () => {
        it('displays popup blocked dialog with correct title and body', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'OK', accept: true } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            await showPopupBlockedDialog();

            expect(mockedShowDialog).toHaveBeenCalledWith({
                title: 'Pop-up Blocked',
                body: 'Your browser blocked the MATLAB pop-up window. Please enable pop-ups for this site and try again.',
                buttons: expect.any(Array)
            });
        });

        it('resolves after user clicks OK', async () => {
            mockedShowDialog.mockResolvedValue({
                button: { label: 'OK', accept: true } as Dialog.IButton,
                value: null,
                isChecked: false
            } as Dialog.IResult<unknown>);

            await expect(showPopupBlockedDialog()).resolves.toBeUndefined();
        });
    });
});
