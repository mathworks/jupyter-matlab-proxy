// Copyright 2023-2024 The MathWorks, Inc.

import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import { matlabToolbarButtonPlugin } from './matlab_browser_button';
import { matlabMFilesPlugin } from './matlab_files';
import { matlabCodeMirror6Plugin } from './matlab_cm6_mode';

const plugins: JupyterFrontEndPlugin<any>[] = [matlabToolbarButtonPlugin, matlabMFilesPlugin, matlabCodeMirror6Plugin];
export default plugins;
