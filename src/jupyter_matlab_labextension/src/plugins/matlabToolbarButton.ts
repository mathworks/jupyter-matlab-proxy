// Copyright 2023-2025 The MathWorks, Inc.

// Registers the button which allows access to MATLAB in a browser, which will
// appear in the notebook toolbar.

import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ToolbarButton } from '@jupyterlab/apputils';
import { PageConfig } from '@jupyterlab/coreutils';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { INotebookModel, NotebookPanel } from '@jupyterlab/notebook';

import { IDisposable } from '@lumino/disposable';

import { matlabIcon } from '../icons';

/** Wait until the kernel has loaded, then check if it is a MATLAB kernel. */
export const insertButton = async (
    panel: NotebookPanel,
    matlabToolbarButton: ToolbarButton
): Promise<void> => {
    await panel.sessionContext.ready;
    if (panel.sessionContext.kernelDisplayName === 'MATLAB Kernel') {
        panel.toolbar.insertItem(10, 'matlabToolbarButton', matlabToolbarButton);
    }
};

export class MatlabToolbarButtonExtension
implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
    createNew (
        panel: NotebookPanel,
        context: DocumentRegistry.IContext<INotebookModel>
    ): IDisposable {
        /**  Create the toolbar button to open MATLAB in a browser. */
        const matlabToolbarButton = new ToolbarButton({
            className: 'openMATLABButton',
            icon: matlabIcon,
            label: 'Open MATLAB',
            tooltip: 'Open MATLAB',
            onClick: (): void => {
                const baseUrl = PageConfig.getBaseUrl();
                // "_blank" is the option to open in a new browser tab
                window.open(baseUrl + 'matlab', '_blank');
            }
        });
        insertButton(panel, matlabToolbarButton);
        return matlabToolbarButton;
    }
}

export const matlabToolbarButtonPlugin: JupyterFrontEndPlugin<void> = {
    id: '@mathworks/matlabToolbarButtonPlugin',
    autoStart: true,
    activate: (app: JupyterFrontEnd) => {
        const matlabToolbarButton = new MatlabToolbarButtonExtension();
        app.docRegistry.addWidgetExtension('Notebook', matlabToolbarButton);
    }
};
