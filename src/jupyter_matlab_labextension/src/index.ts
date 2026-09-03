// Copyright 2023-2026 The MathWorks, Inc.

import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import { matlabToolbarButtonPlugin } from './plugins/matlabToolbarButton';
import { matlabMFilesPlugin } from './plugins/matlabFiles';
import { matlabCodeMirror6Plugin } from './plugins/matlabCM6Mode';
import { matlabCommPlugin } from './plugins/matlabCommunication';
import { matlabExportPlugin } from './plugins/matlabExportButton';

const plugins: JupyterFrontEndPlugin<any>[] = [
    matlabToolbarButtonPlugin,
    matlabMFilesPlugin,
    matlabCodeMirror6Plugin,
    matlabCommPlugin,
    matlabExportPlugin
];
export default plugins;
