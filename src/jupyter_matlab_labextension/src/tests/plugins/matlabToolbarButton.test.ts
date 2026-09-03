// Copyright 2025-2026 The MathWorks, Inc.

import {
    MatlabToolbarButtonExtension,
    matlabToolbarButtonPlugin
} from '../../plugins/matlabToolbarButton';
import { NotebookPanel, INotebookModel } from '@jupyterlab/notebook';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { ToolbarButton } from '@jupyterlab/apputils';
import { Menu } from '@lumino/widgets';
import { Signal } from '@lumino/signaling';

// Mock the icons module
jest.mock('../../icons', () => ({
    matlabIcon: {
        name: 'matlab-icon',
        svgstr: '<svg></svg>'
    }
}));

// Mock JupyterLab dependencies - must be before imports
jest.mock('@jupyterlab/notebook', () => ({
    NotebookPanel: jest.fn(),
    INotebookTracker: Symbol('INotebookTracker')
}));

jest.mock('@jupyterlab/apputils', () => ({
    ToolbarButton: jest.fn().mockImplementation((options: any) => ({
        ...options,
        node: {
            getBoundingClientRect: jest.fn().mockReturnValue({ left: 10, bottom: 20 })
        },
        dispose: jest.fn()
    }))
}));

jest.mock('@jupyterlab/coreutils', () => ({
    PageConfig: {
        getBaseUrl: jest.fn().mockReturnValue('http://localhost:8888/'),
        getOption: jest.fn().mockReturnValue('/home/user')
    }
}));

jest.mock('@lumino/widgets', () => ({
    Menu: jest.fn().mockImplementation(() => ({
        addItem: jest.fn(),
        open: jest.fn(),
        dispose: jest.fn()
    }))
}));

// Mock NotebookInfo
jest.mock('../../utils/notebook', () => ({
    NotebookInfo: jest.fn().mockImplementation(() => ({
        update: jest.fn().mockResolvedValue(undefined),
        isMatlabNotebook: jest.fn().mockReturnValue(true),
        getTargetURL: jest.fn().mockReturnValue('http://localhost:8888/matlab/kernel-123/')
    }))
}));

// Mock commands
jest.mock('../../utils/commands', () => ({
    getOpenMatlabCommandId: jest.fn().mockReturnValue('matlab:open'),
    getOpenAsLiveCodeMLXInMatlabCommandId: jest.fn().mockReturnValue('matlab:openAsLiveCode'),
    openMatlabButtonHandler: jest.fn(),
    openAsLiveCodeInMatlabButtonHandler: jest.fn()
}));

// Mock for NotebookPanel with kernel change signal
const createMockNotebookPanel = (kernelDisplayName = 'MATLAB Kernel', kernelId = '12345') => {
    const kernelChangedSignal = new Signal<any, any>({});

    return {
        id: 'notebook-panel-1',
        context: { path: 'test.ipynb' },
        sessionContext: {
            ready: Promise.resolve(),
            kernelDisplayName,
            session: kernelId
                ? {
                    kernel: {
                        id: kernelId,
                        status: 'idle'
                    }
                }
                : null,
            kernelChanged: kernelChangedSignal,
            initialize: jest.fn(),
            isReady: true,
            isTerminating: false,
            dispose: jest.fn()
        },
        toolbar: {
            insertItem: jest.fn(),
            names: []
        }
    };
};

// Mock for ICommunicationService
const createMockCommService = () => ({
    getComm: jest.fn().mockResolvedValue({})
});

// Mock for JupyterFrontEnd
const createMockJupyterFrontEnd = () => ({
    commands: {
        addCommand: jest.fn()
    },
    shell: {
        currentWidget: null
    },
    docRegistry: {
        addWidgetExtension: jest.fn(),
        changed: { connect: jest.fn() },
        isDisposed: false,
        dispose: jest.fn(),
        addWidgetFactory: jest.fn()
    }
});

// Mock for INotebookTracker
const createMockNotebookTracker = (currentWidget: any = null) => ({
    currentWidget
});

describe('matlabToolbarButton', () => {
    afterEach(() => {
        jest.clearAllMocks();
        // Reset the static commandsRegistered flag
        (MatlabToolbarButtonExtension as any).commandsRegistered = false;
    });

    describe('MatlabToolbarButtonExtension', () => {
        let extension: MatlabToolbarButtonExtension;
        let panel: any;
        let context: any;
        let commService: any;
        let app: any;
        let notebookTracker: any;

        beforeEach(() => {
            commService = createMockCommService();
            app = createMockJupyterFrontEnd();
            panel = createMockNotebookPanel('MATLAB Kernel', 'test-kernel');
            notebookTracker = createMockNotebookTracker(panel);
            extension = new MatlabToolbarButtonExtension(commService, app, notebookTracker);
            context = {};
        });

        test('should return a disposable object', () => {
            const result = extension.createNew(panel, context);

            expect(result.dispose).toBeDefined();
            expect(typeof result.dispose).toBe('function');
        });

        test('should insert toolbar button for MATLAB notebook', async () => {
            extension.createNew(
                panel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            // Wait for async operations
            await panel.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(panel.toolbar.insertItem).toHaveBeenCalledWith(
                10,
                'openMatlabButton',
                expect.any(Object)
            );
        });

        test('should register commands on first createNew call', async () => {
            extension.createNew(
                panel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await panel.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(app.commands.addCommand).toHaveBeenCalledWith(
                'matlab:open',
                expect.objectContaining({
                    label: 'Open MATLAB'
                })
            );
            expect(app.commands.addCommand).toHaveBeenCalledWith(
                'matlab:openAsLiveCode',
                expect.objectContaining({
                    label: 'Open as Live Script in MATLAB'
                })
            );
        });

        test('should not register commands twice', async () => {
            extension.createNew(
                panel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await panel.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            const firstCallCount = app.commands.addCommand.mock.calls.length;

            // Create another panel and call createNew again
            const panel2 = createMockNotebookPanel('MATLAB Kernel', 'test-kernel-2');
            extension.createNew(
                panel2 as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await panel2.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(app.commands.addCommand.mock.calls.length).toBe(firstCallCount);
        });

        test('should create menu with commands', async () => {
            const MenuMock = Menu as unknown as jest.Mock;

            extension.createNew(
                panel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await panel.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(MenuMock).toHaveBeenCalledWith({ commands: app.commands });
            const menuInstance = MenuMock.mock.results[0].value;
            expect(menuInstance.addItem).toHaveBeenCalledWith({ command: 'matlab:open' });
            expect(menuInstance.addItem).toHaveBeenCalledWith({ command: 'matlab:openAsLiveCode' });
        });

        test('should create ToolbarButton with correct options', async () => {
            extension.createNew(
                panel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await panel.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(ToolbarButton).toHaveBeenCalledWith(
                expect.objectContaining({
                    className: 'openMATLABButton matlab-toolbar-button-spaced',
                    label: 'Open MATLAB ▼',
                    tooltip: 'Open MATLAB'
                })
            );
        });

        test('should not insert button for non-MATLAB notebook', async () => {
            const { NotebookInfo } = require('../../utils/notebook');
            NotebookInfo.mockImplementation(() => ({
                update: jest.fn().mockResolvedValue(undefined),
                isMatlabNotebook: jest.fn().mockReturnValue(false),
                getTargetURL: jest.fn().mockReturnValue(undefined)
            }));

            const nonMatlabPanel = createMockNotebookPanel('Python 3', 'python-kernel');
            extension.createNew(
                nonMatlabPanel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await nonMatlabPanel.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(nonMatlabPanel.toolbar.insertItem).not.toHaveBeenCalled();
        });

        test('should log error when kernel is not ready', async () => {
            const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

            const panelWithNoKernel = createMockNotebookPanel('MATLAB Kernel', '');
            panelWithNoKernel.sessionContext.session = null;

            extension.createNew(
                panelWithNoKernel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await panelWithNoKernel.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(consoleErrorSpy).toHaveBeenCalledWith("Kernel not ready! Can't create toolbar button");

            consoleErrorSpy.mockRestore();
        });

        test('should handle errors gracefully', async () => {
            const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

            const panelWithError = {
                sessionContext: {
                    ready: Promise.reject(new Error('Session failed'))
                }
            };

            extension.createNew(
                panelWithError as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await new Promise(resolve => setTimeout(resolve, 10));

            expect(consoleErrorSpy).toHaveBeenCalledWith(
                'Error initializing MATLAB toolbar button:',
                expect.any(Error)
            );

            consoleErrorSpy.mockRestore();
        });

        test('should connect to kernelChanged signal', async () => {
            // Reset NotebookInfo mock to return true for isMatlabNotebook
            const { NotebookInfo } = require('../../utils/notebook');
            NotebookInfo.mockImplementation(() => ({
                update: jest.fn().mockResolvedValue(undefined),
                isMatlabNotebook: jest.fn().mockReturnValue(true),
                getTargetURL: jest.fn().mockReturnValue('http://localhost:8888/matlab/kernel-123/')
            }));

            const freshPanel = createMockNotebookPanel('MATLAB Kernel', 'test-kernel-fresh');
            const connectSpy = jest.spyOn(freshPanel.sessionContext.kernelChanged, 'connect');

            extension.createNew(
                freshPanel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            await freshPanel.sessionContext.ready;
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(connectSpy).toHaveBeenCalled();
        });
    });

    describe('matlabToolbarButtonPlugin', () => {
        test('should have correct id and autoStart properties', () => {
            expect(matlabToolbarButtonPlugin.id).toBe(
                '@mathworks/matlabToolbarButtonPlugin'
            );
            expect(matlabToolbarButtonPlugin.autoStart).toBe(true);
        });

        test('should require IMatlabCommunication', () => {
            expect(matlabToolbarButtonPlugin.requires).toBeDefined();
            expect(matlabToolbarButtonPlugin.requires!.length).toBeGreaterThan(0);
        });

        test('should register extension with docRegistry on activation', () => {
            const app = createMockJupyterFrontEnd();
            const commService = createMockCommService();
            const notebookTracker = createMockNotebookTracker();

            matlabToolbarButtonPlugin.activate(
                app as unknown as JupyterFrontEnd,
                commService,
                notebookTracker as any
            );

            expect(app.docRegistry.addWidgetExtension).toHaveBeenCalledWith(
                'Notebook',
                expect.any(MatlabToolbarButtonExtension)
            );
        });

        test('should create a MatlabToolbarButtonExtension instance on activation', () => {
            const app = createMockJupyterFrontEnd();
            const commService = createMockCommService();
            const notebookTracker = createMockNotebookTracker();

            matlabToolbarButtonPlugin.activate(
                app as unknown as JupyterFrontEnd,
                commService,
                notebookTracker as any
            );

            const extensionArg = (app.docRegistry.addWidgetExtension as jest.Mock)
                .mock.calls[0][1];
            expect(extensionArg).toBeInstanceOf(MatlabToolbarButtonExtension);
        });
    });
});
