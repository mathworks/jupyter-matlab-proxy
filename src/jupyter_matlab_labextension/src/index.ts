// Copyright 2023 The MathWorks, Inc.

import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import { matlabToolbarButtonPlugin } from './matlab_browser_button';
import { matlabMFilesPlugin } from './matlab_files';
import { matlabCodeMirrorPlugin } from './matlab_cm_mode';

const plugins: JupyterFrontEndPlugin<any>[] = [matlabToolbarButtonPlugin, matlabMFilesPlugin, matlabCodeMirrorPlugin];
export default plugins;
