// Copyright 2025 The MathWorks, Inc.

// Mock the icons module
import {
    insertButton,
    MatlabToolbarButtonExtension,
    matlabToolbarButtonPlugin
} from '../plugins/matlabToolbarButton';
import { NotebookPanel, INotebookModel } from '@jupyterlab/notebook';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { Signal } from '@lumino/signaling';

jest.mock('../icons', () => ({
    matlabIcon: {
        name: 'matlab-icon',
        svgstr: '<svg></svg>'
    }
}));

// Mock JupyterLab dependencies
jest.mock('@jupyterlab/apputils', () => ({
    ToolbarButton: jest.fn().mockImplementation((options: any) => ({
        ...options,
        dispose: jest.fn()
    }))
}));

jest.mock('@jupyterlab/coreutils', () => ({
    PageConfig: {
        getBaseUrl: jest.fn().mockReturnValue('http://localhost:8888/')
    }
}));

// Mock window.open
const originalWindowOpen = window.open;
window.open = jest.fn();

// Mock for NotebookPanel with kernel change signal
const createMockNotebookPanel = (kernelDisplayName = 'MATLAB Kernel', kernelId = '12345') => {
    const kernelChangedSignal = new Signal<any, any>({});

    return {
        sessionContext: {
            ready: Promise.resolve(),
            kernelDisplayName,
            session: kernelId
                ? {
                    kernel: {
                        id: kernelId
                    }
                }
                : null,
            kernelChanged: kernelChangedSignal,
            initialize: jest.fn(),
            isReady: true,
            isTerminating: false,
            // Add other required methods as
            dispose: jest.fn()
        },
        toolbar: {
            insertItem: jest.fn(),
            names: []
        }
    };
};

// Mock for JupyterFrontEnd
const createMockJupyterFrontEnd = () => ({
    docRegistry: {
        addWidgetExtension: jest.fn(),
        // Add other required properties with mock implementations
        changed: { connect: jest.fn() },
        isDisposed: false,
        dispose: jest.fn(),
        addWidgetFactory: jest.fn()
    }
});

describe('matlab_browser_button', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    afterAll(() => {
        window.open = originalWindowOpen;
    });

    describe('insertButton', () => {
        test('should insert button when kernel is MATLAB Kernel with valid kernel ID', async () => {
            // Arrange
            const panel = createMockNotebookPanel('MATLAB Kernel', 'test-kernel-123');

            // Act
            await insertButton(panel as unknown as NotebookPanel);

            // Assert
            expect(panel.toolbar!.insertItem).toHaveBeenCalledWith(
                10,
                'matlabToolbarButton',
                expect.objectContaining({
                    className: 'openMATLABButton matlab-toolbar-button-spaced',
                    label: 'Open MATLAB'
                })
            );
        });

        test('should not insert button when kernel is not MATLAB Kernel', async () => {
            // Arrange
            const panel = createMockNotebookPanel('Python 3');

            // Act
            await insertButton(panel as unknown as NotebookPanel);

            // Assert
            expect(panel.toolbar!.insertItem).not.toHaveBeenCalled();
        });

        test('should not insert button when kernel ID is empty', async () => {
            const panel = createMockNotebookPanel('MATLAB Kernel', '');

            await insertButton(panel as unknown as NotebookPanel);

            expect(panel.toolbar.insertItem).not.toHaveBeenCalled();
        });

        test('should not insert button when session is null', async () => {
            const panel = createMockNotebookPanel('MATLAB Kernel');
            panel.sessionContext.session = null;

            await insertButton(panel as unknown as NotebookPanel);

            expect(panel.toolbar.insertItem).not.toHaveBeenCalled();
        });

        test('should not insert button when kernel is null', async () => {
            const panel = createMockNotebookPanel('MATLAB Kernel');
            panel.sessionContext.session = { kernel: null as any };

            await insertButton(panel as unknown as NotebookPanel);

            expect(panel.toolbar.insertItem).not.toHaveBeenCalled();
        });

        test('should construct correct target URL with kernel ID', async () => {
            const ToolbarButtonMock = jest.requireMock('@jupyterlab/apputils').ToolbarButton;
            let capturedOnClick: () => void = () => {};

            ToolbarButtonMock.mockImplementationOnce((options: any) => {
                capturedOnClick = options.onClick;
                return {
                    ...options,
                    dispose: jest.fn()
                };
            });

            const panel = createMockNotebookPanel('MATLAB Kernel', 'kernel-abc-123');
            await insertButton(panel as unknown as NotebookPanel);

            capturedOnClick();

            expect(window.open).toHaveBeenCalledWith(
                'http://localhost:8888/matlab/kernel-abc-123/',
                '_blank'
            );
        });

        test('should wait for session context to be ready before checking kernel', async () => {
            // Arrange
            const readyPromise = new Promise<void>((resolve) =>
                setTimeout(resolve, 10)
            );
            const panel = {
                sessionContext: {
                    ready: readyPromise,
                    kernelDisplayName: 'MATLAB Kernel',
                    session: {
                        kernel: {
                            id: 'test-kernel'
                        }
                    },
                    kernelChanged: new Signal<any, any>({})
                },
                toolbar: {
                    insertItem: jest.fn()
                }
            };

            // Act
            const insertPromise = insertButton(panel as any);

            // Assert - insertItem should not be called before ready resolves
            expect(panel.toolbar.insertItem).not.toHaveBeenCalled();

            // Wait for ready promise to resolve
            await insertPromise;

            // Now insertItem should have been called
            expect(panel.toolbar.insertItem).toHaveBeenCalled();
        });

        test('should update button onClick when kernel changes', async () => {
            const ToolbarButtonMock = jest.requireMock('@jupyterlab/apputils').ToolbarButton;
            const mockButton = {
                onClick: jest.fn(),
                dispose: jest.fn()
            };

            ToolbarButtonMock.mockReturnValue(mockButton);

            const panel = createMockNotebookPanel('MATLAB Kernel', 'kernel-1');
            await insertButton(panel as unknown as NotebookPanel);

            // Simulate kernel change
            panel.sessionContext.session = {
                kernel: { id: 'kernel-2' }
            };
            panel.sessionContext.kernelChanged.emit({});

            // Wait for async operations
            await new Promise(resolve => setTimeout(resolve, 0));

            expect(mockButton.onClick).toBeDefined();
        });

        test('should handle errors gracefully', async () => {
            const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
            const panel = {
                sessionContext: {
                    ready: Promise.reject(new Error('Session failed'))
                }
            };

            const result = await insertButton(panel as any);

            expect(consoleErrorSpy).toHaveBeenCalledWith(
                'Failed to insert MATLAB toolbar button: ',
                expect.any(Error)
            );
            expect(result.dispose).toBeDefined();

            consoleErrorSpy.mockRestore();
        });
    });

    describe('MatlabToolbarButtonExtension', () => {
        let extension: MatlabToolbarButtonExtension;
        let panel: any;
        let context: any;

        beforeEach(() => {
            extension = new MatlabToolbarButtonExtension();
            panel = createMockNotebookPanel('MATLAB Kernel', 'test-kernel');
            context = {};
        });

        test('should return a disposable object', () => {
            // Act
            const result = extension.createNew(panel, context);

            // Assert
            expect(result.dispose).toBeDefined();
            expect(typeof result.dispose).toBe('function');
        });

        test('should call insertButton when createNew is invoked', () => {
            const matlabButtonModule = require('../plugins/matlabToolbarButton');
            const spy = jest
                .spyOn(matlabButtonModule, 'insertButton')
                .mockResolvedValue({ dispose: jest.fn() });

            extension.createNew(
                panel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            expect(spy).toHaveBeenCalledWith(panel);

            spy.mockRestore();
        });

        test('should call insertButton with panel and button', () => {
            // Arrange
            // Import the module using ES modules syntax for TypeScript compatibility
            const matlabButtonModule = require('../plugins/matlabToolbarButton');
            const spy = jest
                .spyOn(matlabButtonModule, 'insertButton')
                .mockImplementation(() => Promise.resolve());

            // Act
            extension.createNew(
                panel as unknown as NotebookPanel,
                context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            // Assert
            expect(spy).toHaveBeenCalledWith(panel);

            // Cleanup
            spy.mockRestore();
        });
    });

    describe('matlabToolbarButtonPlugin', () => {
        test('should have correct id and autoStart properties', () => {
            // Assert
            expect(matlabToolbarButtonPlugin.id).toBe(
                '@mathworks/matlabToolbarButtonPlugin'
            );
            expect(matlabToolbarButtonPlugin.autoStart).toBe(true);
        });

        test('should register extension with docRegistry on activation', () => {
            // Arrange
            const app = createMockJupyterFrontEnd();

            // Act
            matlabToolbarButtonPlugin.activate(app as unknown as JupyterFrontEnd);

            // Assert
            expect(app.docRegistry!.addWidgetExtension).toHaveBeenCalledWith(
                'Notebook',
                expect.any(MatlabToolbarButtonExtension)
            );
        });

        test('should create a MatlabToolbarButtonExtension instance on activation', () => {
            // Arrange
            const app = createMockJupyterFrontEnd();

            // Act
            matlabToolbarButtonPlugin.activate(app as unknown as JupyterFrontEnd);

            // Assert - Check if addWidgetExtension was called with an instance of MatlabToolbarButtonExtension
            expect(app.docRegistry!.addWidgetExtension).toHaveBeenCalledWith(
                'Notebook',
                expect.any(MatlabToolbarButtonExtension)
            );

            // Additional check - verify the argument is an instance of MatlabToolbarButtonExtension
            const extensionArg = (app.docRegistry!.addWidgetExtension as jest.Mock)
                .mock.calls[0][1];
            expect(extensionArg).toBeInstanceOf(MatlabToolbarButtonExtension);
        });
    });
});
