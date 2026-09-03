// Copyright 2026 The MathWorks, Inc.

import { startMatlab, waitForMatlabToStart, convertToLiveCodeAndOpenMatlab, waitForUserToSignin } from './matlab';
import { NotebookPanel } from '@jupyterlab/notebook';
import { NotebookInfo } from '../utils/notebook';
import { getFileNameForConversion } from './file';
import { ICommunicationService } from '../plugins/matlabCommunication';
import { displayUserSigninNotification } from './notifications';
import { showMatlabKernelIsBusyDialog, showPopupBlockedDialog } from './dialogs';

export function getOpenMatlabCommandId (): string {
    return 'matlab:open-matlab';
}

export function getOpenAsLiveCodeMLXInMatlabCommandId (): string {
    return 'matlab:open-as-live-code-mlx';
}

export function getOpenAsLiveCodeMInMatlabCommandId (): string {
    return 'matlab:open-as-live-code-m';
}

export function exportAsLiveCodeMlxMenuItemCommandId (): string {
    return 'matlab-menu-item:export-to-live-code-mlx';
}

export function exportAsLiveCodeMMenuItemCommandId (): string {
    return 'matlab-menu-item:export-to-live-code-m';
}

export function exportAsLiveCodeMlxPaletteItemCommandId (): string {
    return 'matlab-palette-item:export-to-live-code-mlx';
}

export function exportAsLiveCodeMPaletteItemCommandId (): string {
    return 'matlab-palette-item:export-to-live-code-m';
}

export async function openMatlabInNewTab (targetURL: string): Promise<globalThis.Window | null> {
    const matlabTab = window.open(targetURL, '_blank');
    // If popups were blocked by the user, inform them using a dialog box.
    if (!matlabTab || matlabTab.closed) {
        await showPopupBlockedDialog();
        return null;
    }
    return matlabTab;
}

export async function openAsLiveCodeInMatlabButtonHandler (
    panel: NotebookPanel,
    commService: ICommunicationService
): Promise<void> {
    const notebookInfo = new NotebookInfo();
    await notebookInfo.update(panel);

    if (notebookInfo.isBusy()) {
        await showMatlabKernelIsBusyDialog();
        return;
    }
    const comm = await commService.getComm(panel.id);
    const finalLiveCodeFilePath = await getFileNameForConversion(
        panel,
        comm
    );

    if (!finalLiveCodeFilePath) {
        return; // User aborted the conversion, so return early..
    }

    const status = await startMatlab(panel, comm);
    if (!status.isMatlabLicensed) {
        const userSigninPromise = await displayUserSigninNotification();
        // No need to keep the window reference here as matlab window is
        // required to display to the liveCode file in the editor
        const matlabTab = await openMatlabInNewTab(notebookInfo.getTargetURL()!);
        // If matlabTab is null, it means that popups were blocked by the browser, so do not
        // proceed with the rest of the flow.
        if (!matlabTab || matlabTab.closed) {
            return;
        }
        await waitForUserToSignin(1000, comm, userSigninPromise);
        await waitForMatlabToStart(1000, comm, panel);

        await convertToLiveCodeAndOpenMatlab(panel, comm, finalLiveCodeFilePath, false);
    } else {
        await waitForMatlabToStart(1000, comm, panel);
        await convertToLiveCodeAndOpenMatlab(panel, comm, finalLiveCodeFilePath, true);
    }
}
