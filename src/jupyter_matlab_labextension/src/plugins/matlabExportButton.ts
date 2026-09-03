// Copyright 2026 The MathWorks, Inc.

import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ICommandPalette } from '@jupyterlab/apputils';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { INotebookTracker } from '@jupyterlab/notebook';
import { Menu } from '@lumino/widgets';
import { IMatlabCommunication, ICommunicationService } from './matlabCommunication';
import { exportHandler } from '../utils/export';
import { NotebookInfo } from '../utils/notebook';
import { exportAsLiveCodeMlxMenuItemCommandId, exportAsLiveCodeMlxPaletteItemCommandId } from '../utils/commands';

export const matlabExportPlugin: JupyterFrontEndPlugin<void> = {
    id: '@mathworks/MLXExportPlugin',
    autoStart: true,
    requires: [
        ICommandPalette,
        IMainMenu,
        INotebookTracker,
        IMatlabCommunication
    ],
    activate: async (
        app: JupyterFrontEnd,
        palette: ICommandPalette,
        mainMenu: IMainMenu,
        notebookTracker: INotebookTracker,
        commService: ICommunicationService
    ) => {
        console.debug('Activated MATLAB Export Plugin');
        const notebookInfo = new NotebookInfo();

        // Initialize with current notebook if it exists
        if (notebookTracker.currentWidget) {
            await notebookTracker.currentWidget.context.ready;
            await notebookInfo.update(notebookTracker.currentWidget);
        } else {
            console.debug('No active notebook on plugin activation');
        }

        const { commands } = app;
        const fileMenu = mainMenu.fileMenu;

        commands.addCommand(exportAsLiveCodeMlxPaletteItemCommandId(), {
            label: 'Save and Export Notebook: MATLAB Live Script',
            execute: async () => {
                await exportHandler(commService, notebookTracker.currentWidget);
            },
            isEnabled: () => notebookInfo.isMatlabNotebook()
        });

        palette.addItem({ command: exportAsLiveCodeMlxPaletteItemCommandId(), category: 'File' });

        // Add command to the jupyterlab file menu
        let exportSubmenu: Menu | undefined;

        fileMenu.items.forEach((item) => {
            if (item.type === 'submenu' && item.submenu) {
                const submenu = item.submenu;
                if (submenu.title.label === 'Save and Export Notebook As') {
                    exportSubmenu = submenu;
                }
            }
        });

        if (exportSubmenu) {
            commands.addCommand(exportAsLiveCodeMlxMenuItemCommandId(), {
                label: 'MATLAB Live Script',
                execute: async () => {
                    await exportHandler(commService, notebookTracker.currentWidget);
                },
                isEnabled: () => notebookInfo.isMatlabNotebook()
            });
            exportSubmenu.addItem({ command: exportAsLiveCodeMlxMenuItemCommandId() });
        }

        // Set up listeners for current and future notebooks
        notebookTracker.widgetAdded.connect((_, notebookPanel) => {
            notebookPanel.context.ready.then(() => {
                notebookInfo.update(notebookPanel);
            });
        });

        // Add state change listener to update whether commands should be enabled or disabled
        // based on the type of notebook currently active
        notebookTracker.currentChanged.connect(async (_, notebookPanel) => {
            if (notebookPanel) {
                await notebookPanel.context.ready;
            }
            notebookInfo.update(notebookPanel);
            if (commands.hasCommand(exportAsLiveCodeMlxPaletteItemCommandId())) {
                commands.notifyCommandChanged(exportAsLiveCodeMlxPaletteItemCommandId());
            }

            if (commands.hasCommand(exportAsLiveCodeMlxMenuItemCommandId())) {
                commands.notifyCommandChanged(exportAsLiveCodeMlxMenuItemCommandId());
            }
        });
    }
};
