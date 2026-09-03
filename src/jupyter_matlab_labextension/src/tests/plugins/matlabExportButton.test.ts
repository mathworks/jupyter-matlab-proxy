// Copyright 2026 The MathWorks, Inc.

import { matlabExportPlugin } from '../../plugins/matlabExportButton';
import { ICommunicationService } from '../../plugins/matlabCommunication';

// ---------- MOCKS ----------

jest.mock('@jupyterlab/notebook', () => ({
    NotebookPanel: jest.fn(),
    INotebookTracker: jest.fn()
}));

jest.mock('@lumino/widgets', () => ({
    Menu: jest.fn().mockImplementation(() => ({
        addItem: jest.fn()
    }))
}));

jest.mock('@jupyterlab/mainmenu', () => ({
    IMainMenu: jest.fn().mockImplementation(() => ({
        fileMenu: jest.fn().mockReturnValue([
            {
                type: 'submenu',
                submenu: {
                    title: { label: 'Save and Export Notebook As' },
                    addItem: jest.fn()
                }
            }
        ])
    }))
}));

jest.mock('../../utils/file', () => ({
    getFileNameForConversion: jest.fn()
}));

jest.mock('../../utils/matlab', () => ({
    convertToLiveCode: jest.fn(),
    startMatlab: jest.fn(),
    waitForMatlabToStart: jest.fn(),
    waitForUserToSignin: jest.fn()
}));

jest.mock('../../utils/notifications', () => ({
    displayKernelBusyNotification: jest.fn(),
    displayUserSigninNotification: jest.fn()
}));

jest.mock('@jupyterlab/apputils', () => ({
    Notification: { info: jest.fn() }
}));

describe('matlabExportPlugin', () => {
    let app: any;
    let palette: any;
    let mainMenu: any;
    let notebookTracker: any;
    let commService: any;

    beforeEach(() => {
        jest.clearAllMocks();

        app = {
            commands: {
                addCommand: jest.fn(),
                hasCommand: jest.fn().mockReturnValue(true),
                notifyCommandChanged: jest.fn()
            }
        };

        palette = { addItem: jest.fn() };

        mainMenu = {
            fileMenu: {
                items: [{
                    type: 'submenu',
                    submenu: { title: { label: 'Save and Export Notebook As' }, addItem: jest.fn() }
                }]
            }
        };

        notebookTracker = {
            currentWidget: {
                context: { ready: Promise.resolve() },
                sessionContext: {
                    isReady: false,
                    ready: Promise.resolve(),
                    session: {
                        kernel: null
                    }
                }
            },
            widgetAdded: { connect: jest.fn() },
            currentChanged: { connect: jest.fn() }
        };

        commService = {} as ICommunicationService;
    });

    // --------------------------
    // ACTIVATE TEST
    // --------------------------
    it('activates and registers commands, palette items, menu items', async () => {
        await matlabExportPlugin.activate(
            app,
            palette,
            mainMenu,
            notebookTracker,
            commService
        );

        // palette command registered
        expect(app.commands.addCommand).toHaveBeenCalledTimes(2);
        expect(palette.addItem).toHaveBeenCalledTimes(1);

        // menu item added
        const submenu = mainMenu.fileMenu.items[0].submenu;
        expect(submenu.addItem).toHaveBeenCalledTimes(1);

        // listeners installed
        expect(notebookTracker.widgetAdded.connect).toHaveBeenCalled();
        expect(notebookTracker.currentChanged.connect).toHaveBeenCalled();
    });

    it('should debug log when there is no widget and buttons should not be enabled', async () => {
        const debugSpy = jest.spyOn(console, 'debug').mockImplementation(() => {});

        notebookTracker.currentWidget = null;
        await matlabExportPlugin.activate(
            app,
            palette,
            mainMenu,
            notebookTracker,
            commService
        );

        // palette command registered
        expect(app.commands.addCommand).toHaveBeenCalledTimes(2);
        expect(palette.addItem).toHaveBeenCalledTimes(1);

        // menu item added
        const submenu = mainMenu.fileMenu.items[0].submenu;
        expect(submenu.addItem).toHaveBeenCalledTimes(1);

        // listeners installed
        expect(notebookTracker.widgetAdded.connect).toHaveBeenCalled();
        expect(notebookTracker.currentChanged.connect).toHaveBeenCalled();

        expect(debugSpy).toHaveBeenCalled();
        expect(debugSpy).toHaveBeenCalledWith('No active notebook on plugin activation');

        expect(app.commands.addCommand.mock.calls[0][1].isEnabled()).toBe(false);
        expect(app.commands.addCommand.mock.calls[1][1].isEnabled()).toBe(false);
    });

    it('should not add export option to FileMenu when no submenu for export is found', async () => {
        mainMenu = {
            fileMenu: {
                items: [{
                    type: 'menu',
                    submenu: { title: { label: 'File' }, addItem: jest.fn() }
                }]
            }
        };

        notebookTracker.currentWidget = null;
        await matlabExportPlugin.activate(
            app,
            palette,
            mainMenu,
            notebookTracker,
            commService
        );

        // palette command registered
        expect(app.commands.addCommand).toHaveBeenCalledTimes(1);
        expect(palette.addItem).toHaveBeenCalledTimes(1);

        // menu item added
        const submenu = mainMenu.fileMenu.items[0].submenu;
        expect(submenu.addItem).toHaveBeenCalledTimes(0);

        // listeners installed
        expect(notebookTracker.widgetAdded.connect).toHaveBeenCalled();
        expect(notebookTracker.currentChanged.connect).toHaveBeenCalled();
    });
});
