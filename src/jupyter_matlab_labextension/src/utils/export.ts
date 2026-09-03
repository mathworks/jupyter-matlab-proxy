// Copyright 2026 The MathWorks, Inc.

import { NotebookPanel } from '@jupyterlab/notebook';
import { ICommunicationService } from '../plugins/matlabCommunication';
import { displayUserSigninNotification } from './notifications';
import { showMatlabKernelIsBusyDialog } from './dialogs';
import { openMatlabInNewTab } from './commands';
import { getFileNameForConversion } from '../utils/file';
import { convertToLiveCode, startMatlab, waitForMatlabToStart, waitForUserToSignin } from '../utils/matlab';
import { NotebookInfo } from './notebook';
import { Notification } from '@jupyterlab/apputils';

export async function exportHandler (
    commService: ICommunicationService,
    panel: NotebookPanel | null
): Promise<void> {
    if (!panel) {
        console.error('No active notebook to export');
        return;
    }
    const notebookInfo = new NotebookInfo();
    await notebookInfo.update(panel);
    await panel.context.save();

    if (notebookInfo.isBusy()) {
        await showMatlabKernelIsBusyDialog();
        return;
    }
    const comm = await commService.getComm(panel.id);

    const finalMlxFilePath = await getFileNameForConversion(
        panel,
        comm
    );
    if (!finalMlxFilePath) {
        return; // User aborted the conversion, so return early..
    }

    const status = await startMatlab(panel, comm);

    if (!status.isMatlabLicensed) {
        const userSigninPromise = await displayUserSigninNotification();

        const window = await openMatlabInNewTab(notebookInfo.getTargetURL()!);
        // If Pop up is blocked or the user closed the tab, do not proceed with the rest of the flow
        if (!window || window.closed) {
            return;
        }

        // Wait for the user to complete sign in
        await waitForUserToSignin(1000, comm, userSigninPromise);

        // As this is export workflow, it is not required to open the matlab editor.
        // So, close the window once sign in is done and proceed starting matlab and conversion to mlx
        if (window && !window.closed) {
            window.close();
        }
    }

    await waitForMatlabToStart(1000, comm, panel);
    const livecodeFilePath = await convertToLiveCode(panel, comm, notebookInfo.getCurrentFilePath()!, finalMlxFilePath);
    Notification.info(`File ${livecodeFilePath} ready`, { autoClose: 2000 });
}
