// Copyright 2026 The MathWorks, Inc.

import { ICommunicationChannel } from '../plugins/matlabCommunication';
import { NotebookPanel } from '@jupyterlab/notebook';
import { ActionFactory } from '../plugins/actions/actionFactory';
import { ActionTypes } from '../plugins/actions/actionTypes';
import { MATLABStatus, MatlabStatusAction } from '../plugins/actions/matlabStatusAction';

import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';
import { displayOpenMatlabNotification, displayStartingMatlabNotification } from './notifications';
import { ConvertAction } from '../plugins/actions/convertAction';
import { NotebookInfo } from './notebook';
import { openMatlabInNewTab } from './commands';

export async function getMatlabProxyStatus (panel: NotebookPanel, comm: ICommunicationChannel): Promise<MATLABStatus> {
    const matlabStatusAction = ActionFactory.createAction(
        ActionTypes.MATLAB_STATUS,
        true
    );
    await matlabStatusAction.execute(null, comm);
    return MatlabStatusAction.getStatus();
}

export async function startMatlab (
    notebook: NotebookPanel,
    comm: ICommunicationChannel
): Promise<MATLABStatus> {
    // Send StartMatlabProxy action to kernel. This would be a no-op if matlab-proxy is already up
    const startMatlabProxyAction = ActionFactory.createAction(
        ActionTypes.START_MATLAB_PROXY,
        true
    );
    await startMatlabProxyAction.execute(null, comm);

    // Get status of matlab-proxy
    const status = await getMatlabProxyStatus(notebook, comm);
    return status;
}

export async function waitForMatlabToStart (
    sleepInMS: number,
    comm: ICommunicationChannel,
    notebook: NotebookPanel
): Promise<void> {
    const matlabStatusAction = ActionFactory.createAction(
        ActionTypes.MATLAB_STATUS,
        true
    );
    const matlabStartPromise = displayStartingMatlabNotification();

    let timeoutReached = false;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    // eslint-disable-next-line no-unmodified-loop-condition
    while (!timeoutReached) {
        await matlabStatusAction.execute(null, comm);
        const status = MatlabStatusAction.getStatus();

        // Arm the timeout once, using matlab-proxy's own configured process start
        // timeout (MWI_PROCESS_START_TIMEOUT, reported in seconds). Fall back to
        // 10 minutes if the status request failed to report a value.
        if (timeoutId === undefined) {
            const timeoutInMS = (status?.processStartTimeout ?? 600) * 1000;
            timeoutId = setTimeout(() => {
                matlabStartPromise.reject(
                    new Error('Timed out waiting for MATLAB to start')
                );
                timeoutReached = true;
            }, timeoutInMS);
        }

        if (status.matlabStatus === 'up') {
            clearTimeout(timeoutId);
            matlabStartPromise.resolve(null);
            break;
        }
        await new Promise((resolve) => setTimeout(resolve, sleepInMS));
    }
}

export async function convertToLiveCodeAndOpenMatlab (
    notebook: NotebookPanel,
    comm: ICommunicationChannel,
    liveCodeFilePath: string,
    shouldOpenMatlab: boolean = true
): Promise<void> {
    const notebookInfo = new NotebookInfo();
    await notebookInfo.update(notebook);
    const generatedLiveCodeFilePath = await convertToLiveCode(notebook, comm, notebookInfo.getCurrentFilePath()!, liveCodeFilePath);

    if (generatedLiveCodeFilePath) {
        if (shouldOpenMatlab) {
            displayOpenMatlabNotification();
            // 1500ms or 1.5sec delay before opening a new tab for better UX.
            await new Promise(resolve => setTimeout(resolve, 1500));
            const matlabTab = await openMatlabInNewTab(notebookInfo.getTargetURL()!);
            if (!matlabTab || matlabTab.closed) {
                return;
            }
        }

        await openGeneratedFileInEditor(notebook, comm, generatedLiveCodeFilePath);
    }
}

export async function openGeneratedFileInEditor (
    notebook: NotebookPanel,
    comm: ICommunicationChannel,
    liveCodeFilePath: string): Promise<void> {
    const editAction = ActionFactory.createAction(
        ActionTypes.EDIT,
        true
    );
    await editAction.execute(
        { action: ActionTypes.EDIT, liveCodeFilePath },
        comm
    );
}

export async function convertToLiveCode (
    notebook: NotebookPanel,
    comm: ICommunicationChannel,
    ipynbFilePath: string,
    liveCodeFilePath: string
): Promise<string> {
    const convertAction = ActionFactory.createAction(
        ActionTypes.CONVERT,
        true
    );
    await convertAction.execute(
        {
            ipynbFilePath,
            liveCodeFilePath
        },
        comm
    );

    return ConvertAction.getGeneratedLiveCodeFilePath();
}

export async function waitForUserToSignin (sleepInMS: number,
    comm: ICommunicationChannel,
    promise: PromiseDelegate<ReadonlyJSONValue>,
    timeoutInMS: number = 600000 // Default timeout for User to finish Signin is 10 minutes
): Promise<void> {
    const matlabStatusAction = ActionFactory.createAction(
        ActionTypes.MATLAB_STATUS,
        true
    );

    let timeoutReached = false;

    // Setup a timeout to reject the promise and return from this function
    // if MATLAB does not start within the specified timeoutInMS
    setTimeout(() => {
        promise.reject(
            new Error('Timed out waiting for user to finish signin')
        );
        timeoutReached = true;
    }, timeoutInMS);

    // eslint-disable-next-line no-unmodified-loop-condition
    while (!timeoutReached) {
        await matlabStatusAction.execute(null, comm);
        const status = MatlabStatusAction.getStatus();
        if (status.isMatlabLicensed) {
            promise.resolve(null);
            break;
        }
        await new Promise((resolve) => setTimeout(resolve, sleepInMS));
    }
}
