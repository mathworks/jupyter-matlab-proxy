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

import { DisposableDelegate } from '@lumino/disposable';

import { matlabIcon } from '../icons';

function createMATLABToolbarButton (targetUrl: string): ToolbarButton {
    return new ToolbarButton({
        className: 'openMATLABButton matlab-toolbar-button-spaced',
        icon: matlabIcon,
        label: 'Open MATLAB',
        tooltip: 'Open MATLAB',
        onClick: (): void => {
            window.open(targetUrl, '_blank');
        }
    });
}

/** Wait until the kernel has loaded, then check if it is a MATLAB kernel. */
export const insertButton = async (panel: NotebookPanel): Promise<DisposableDelegate> => {
    try {
        await panel.sessionContext.ready;
        let targetUrl = '';
        let matlabToolbarButton: ToolbarButton | null = null;

        // Function to update the target URL based on kernel ID
        const updateTargetUrl = (): void => {
            // Check if the kernel is a MATLAB Kernel
            if (panel.sessionContext.kernelDisplayName === 'MATLAB Kernel') {
                let kernelId = '';

                // Check that session and kernel exist and then retrieve kernel ID
                if (panel.sessionContext.session && panel.sessionContext.session.kernel) {
                    kernelId = panel.sessionContext.session.kernel.id;
                }

                if (kernelId !== '') {
                    targetUrl = PageConfig.getBaseUrl() + 'matlab/' + kernelId + '/';

                    // Create the button if it doesn't exist yet
                    if (!matlabToolbarButton) {
                        matlabToolbarButton = createMATLABToolbarButton(targetUrl);
                        panel.toolbar.insertItem(10, 'matlabToolbarButton', matlabToolbarButton);
                    } else {
                        // Update the button's onClick handler
                        matlabToolbarButton.onClick = () => {
                            window.open(targetUrl, '_blank');
                        };
                    }
                }
            }
        };

        // Create Open MATLAB toolbar button
        updateTargetUrl();

        // Listen for kernel changes
        panel.sessionContext.kernelChanged.connect(() => {
            updateTargetUrl();
        });

        // Create a disposable that will clean up the listener
        return new DisposableDelegate(() => {
            if (matlabToolbarButton) {
                matlabToolbarButton.dispose();
            }
            panel.sessionContext.kernelChanged.disconnect(() => {
                updateTargetUrl();
            });
        });
    } catch (error) {
        console.error('Failed to insert MATLAB toolbar button: ', error);
        return new DisposableDelegate(() => {});
    }
};

export class MatlabToolbarButtonExtension
implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
    createNew (
        panel: NotebookPanel,
        context: DocumentRegistry.IContext<INotebookModel>
    ): DisposableDelegate {
        /**  Create the toolbar button to open MATLAB in a browser. */
        insertButton(panel).catch(error => {
            console.error('Error inserting MATLAB toolbar button:', error);
        });
        // Return a dummy disposable immediately
        return new DisposableDelegate(() => {});
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
