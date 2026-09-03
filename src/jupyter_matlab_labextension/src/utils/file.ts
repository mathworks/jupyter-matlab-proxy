// Copyright 2026 The MathWorks, Inc.

import { NotebookPanel } from '@jupyterlab/notebook';
import { ICommunicationChannel } from '../plugins/matlabCommunication';
import { ActionFactory } from '../plugins/actions/actionFactory';
import { ActionTypes } from '../plugins/actions/actionTypes';
import { CheckFileExistsAction } from '../plugins/actions/checkFileExistsAction';
import { getNewFileNameDialog } from './dialogs';
import { NotebookInfo } from './notebook';
import path from 'path';

export async function getFileNameForConversion (
    panel: NotebookPanel,
    comm: ICommunicationChannel
): Promise<string | null> {
    const notebookInfo = new NotebookInfo();
    await notebookInfo.update(panel);
    const ipynbFilePath = notebookInfo.getCurrentFilePath()!;
    const checkFileExistsAction = ActionFactory.createAction(
        ActionTypes.CHECK_FILE_EXISTS,
        true
    );
    await checkFileExistsAction.execute({ ipynbFilePath }, comm);
    const fileAlreadyExists = CheckFileExistsAction.getFileExistsStatus();

    if (fileAlreadyExists) {
        const newFileName = await getNewFileNameDialog(notebookInfo.getCurrentFilename()!);
        console.debug('New file name chosen by the user is ', newFileName);
        if (newFileName) {
            return path.join(notebookInfo.getCurrentDirectory()!, newFileName);
        } else {
            return null; // User neither provided a new file name nor chose to overwrite, so return null
        }
    } else {
        return ipynbFilePath.replace('.ipynb', '.mlx');
    }
}
