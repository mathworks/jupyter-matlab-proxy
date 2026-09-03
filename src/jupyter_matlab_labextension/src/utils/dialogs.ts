// Copyright 2026 The MathWorks, Inc.

import { showDialog, Dialog, InputDialog } from '@jupyterlab/apputils';
import { PathExt } from '@jupyterlab/coreutils';

export async function getNewFileNameDialog (
    currentFileName: string
): Promise<string | null> {
    const mlxFileNameWithoutExtension = currentFileName.split('.')[0];
    const result = await showDialog({
        title: `"${mlxFileNameWithoutExtension}" Live Script file already exists.`,
        body: `A file named "${mlxFileNameWithoutExtension}" Live Script already exists in the folder. Choose a new name or replace it to overwrite its current contents`,
        buttons: [
            Dialog.cancelButton(),
            Dialog.okButton({ label: 'Replace' }),
            Dialog.okButton({ label: 'New Name' })
        ]
    });

    if (result.button.label === 'New Name') {
        const newNameResult = await InputDialog.getText({
            title: 'New File Name',
            label: 'Choose a new name for the file. Do not include a file extension',
            placeholder: 'Enter file name',
            // Enforce a valid MATLAB function name natively: must start with a
            // letter, followed by up to 62 letters/digits/underscores (max
            // length 63). The browser disables "OK" until the input matches.
            pattern: '[A-Za-z][A-Za-z0-9_]{0,62}',
            required: true
        });

        if (newNameResult.button.accept && newNameResult.value) {
            // The regex above already rules out path separators and
            // extensions, but keep PathExt.basename() as a defense-in-depth
            // guard against any input that bypasses validation (e.g. paste).
            const name = PathExt.basename(newNameResult.value.trim());

            console.debug(
                'new file name is ',
                name,
                ' currentfilename is ',
                currentFileName
            );

            return `${name}.m`;
        } else {
            // User cancelled, no need to proceed further
            return null;
        }
    } else if (result.button.label === 'Replace') {
        // User chose to replace the existing file
        const mlxFileNameWithoutExtension = PathExt.basename(
            currentFileName,
            PathExt.extname(currentFileName)
        );
        return `${mlxFileNameWithoutExtension}.m`;
    } else {
        return null; // User cancelled, no need to proceed further
    }
}

export async function showMatlabKernelIsBusyDialog (): Promise<void> {
    await showDialog({
        title: 'MATLAB Kernel Busy',
        body: 'The MATLAB kernel must be idle to open the Notebook as Live Script in MATLAB. Try again when the MATLAB kernel is idle.',
        buttons: [Dialog.okButton()]
    });
}

export async function showPopupBlockedDialog (): Promise<void> {
    await showDialog({
        title: 'Pop-up Blocked',
        body: 'Your browser blocked the MATLAB pop-up window. Please enable pop-ups for this site and try again.',
        buttons: [Dialog.okButton()]
    });
}
