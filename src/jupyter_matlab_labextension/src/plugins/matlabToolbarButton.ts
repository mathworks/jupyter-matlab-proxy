// Copyright 2023-2026 The MathWorks, Inc.

// Registers the button which allows access to MATLAB in a browser, which will
// appear in the notebook toolbar.

import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ToolbarButton } from '@jupyterlab/apputils';
// import { PageConfig } from '@jupyterlab/coreutils';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { INotebookModel, NotebookPanel, INotebookTracker } from '@jupyterlab/notebook';
import { DisposableDelegate } from '@lumino/disposable';
import { Menu } from '@lumino/widgets';

import { IMatlabCommunication, ICommunicationService } from './matlabCommunication';
import { NotebookInfo } from '../utils/notebook';
import { getOpenAsLiveCodeMLXInMatlabCommandId, getOpenMatlabCommandId, openAsLiveCodeInMatlabButtonHandler, openMatlabInNewTab } from '../utils/commands';

import { matlabIcon } from '../icons';

export class MatlabToolbarButtonExtension
implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
    private readonly commService: ICommunicationService;
    private readonly app: JupyterFrontEnd;
    private readonly notebookTracker: INotebookTracker;
    // Keep track of whether commands have been registered
    private static commandsRegistered = false;

    constructor (commService: ICommunicationService, app: JupyterFrontEnd, notebookTracker: INotebookTracker) {
        this.commService = commService;
        this.app = app;
        this.notebookTracker = notebookTracker;
    }

    createNew (
        panel: NotebookPanel,
        context: DocumentRegistry.IContext<INotebookModel>
    ): DisposableDelegate {
        panel.sessionContext.ready
            .then(async () => {
                const kernel = panel.sessionContext.session?.kernel;

                // If kernel is available, create channel and set up listeners.
                if (!kernel) {
                    console.error("Kernel not ready! Can't create toolbar button");
                    return new DisposableDelegate(() => {});
                }

                const notebookInfo = new NotebookInfo();
                await notebookInfo.update(panel);

                if (!notebookInfo.isMatlabNotebook()) {
                    console.debug('Not a MATLAB notebook, skipping button setup');
                    return new DisposableDelegate(() => {});
                }

                if (!MatlabToolbarButtonExtension.commandsRegistered) {
                    this.app.commands.addCommand(getOpenMatlabCommandId(), {
                        label: 'Open MATLAB',
                        className: 'openMATLABButton matlab-toolbar-button-spaced',
                        icon: matlabIcon,
                        execute: async () => {
                            const currentPanel = this.notebookTracker.currentWidget;
                            if (!currentPanel) {
                                console.error('No active notebook panel');
                                return;
                            }
                            await notebookInfo.update(currentPanel);
                            // Ignoring the window return value as there isn't anything to do after.
                            await openMatlabInNewTab(notebookInfo.getTargetURL()!);
                        }
                    });

                    this.app.commands.addCommand(getOpenAsLiveCodeMLXInMatlabCommandId(), {
                        label: 'Open as Live Script in MATLAB',
                        className: 'openMATLABButton matlab-toolbar-button-spaced',
                        icon: matlabIcon,
                        execute: async () => {
                            const currentPanel = this.notebookTracker.currentWidget;
                            if (!currentPanel) {
                                console.error('No active notebook panel');
                                return;
                            }
                            // Save the notebook and then begin conversion.
                            await currentPanel.context.save();
                            await openAsLiveCodeInMatlabButtonHandler(currentPanel, this.commService);
                        }
                    });

                    MatlabToolbarButtonExtension.commandsRegistered = true;
                }

                // Create the menu for this notebook toolbar button
                const menu = new Menu({ commands: this.app.commands });
                menu.addItem({ command: getOpenMatlabCommandId() });
                menu.addItem({ command: getOpenAsLiveCodeMLXInMatlabCommandId() });

                /**  Create the toolbar button to show the drop down menu created above */
                const matlabToolbarButton = new ToolbarButton({
                    className: 'openMATLABButton matlab-toolbar-button-spaced',
                    icon: matlabIcon,
                    label: 'Open MATLAB ▼',
                    tooltip: 'Open MATLAB',
                    onClick: (): void => {
                        // On button click, open the menu and position it below the button
                        const buttonElement = matlabToolbarButton.node;
                        const rect = buttonElement.getBoundingClientRect();
                        menu.open(rect.left, rect.bottom);
                    }
                });
                panel.toolbar.insertItem(10, 'openMatlabButton', matlabToolbarButton);

                // Listen for kernel changes
                panel.sessionContext.kernelChanged.connect(async () => {
                    await notebookInfo.update(panel);
                });

                return new DisposableDelegate(() => {
                    matlabToolbarButton.dispose();
                    menu.dispose();
                });
            }).catch((error) => {
                console.error('Error initializing MATLAB toolbar button:', error);
                return new DisposableDelegate(() => {});
            });

        // Return a dummy disposable immediately
        return new DisposableDelegate(() => {});
    }
}

export const matlabToolbarButtonPlugin: JupyterFrontEndPlugin<void> = {
    id: '@mathworks/matlabToolbarButtonPlugin',
    autoStart: true,
    requires: [IMatlabCommunication, INotebookTracker],
    activate: (app: JupyterFrontEnd, commService: ICommunicationService, notebookTracker: INotebookTracker) => {
        const matlabToolbarButton = new MatlabToolbarButtonExtension(commService, app, notebookTracker);
        app.docRegistry.addWidgetExtension('Notebook', matlabToolbarButton);
    }
};
