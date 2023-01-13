// Copyright 2023 The MathWorks, Inc.

import { LabIcon } from '@jupyterlab/ui-components';

import membraneSvgStr from '../style/icons/membrane.svg';
import newMFileSvgStr from '../style/icons/icon_new_mfile.svg';
import notebookSvgStr from '../style/icons/icon_notebook.svg';
import openMATLABSvgStr from '../style/icons/icon_open_matlab.svg';

export const matlabIcon = new LabIcon({
    name: 'matlabIcon',
    svgstr: membraneSvgStr
});

export const openMATLABIcon = new LabIcon({
    name: 'openMATLABIcon',
    svgstr: openMATLABSvgStr
});

export const newMFileIcon = new LabIcon({
    name: 'newMFileIcon',
    svgstr: newMFileSvgStr
});

export const notebookIcon = new LabIcon({
    name: 'notebookIcon',
    svgstr: notebookSvgStr
});
