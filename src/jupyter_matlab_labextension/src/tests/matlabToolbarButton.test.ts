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

jest.mock('../icons', () => ({
    matlabIcon: {
        name: 'matlab-icon',
        svgstr: '<svg></svg>'
    }
}));

// Get the mocked matlabIcon
const { matlabIcon } = jest.requireMock('../icons');

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

// Mock for NotebookPanel
const createMockNotebookPanel = (kernelDisplayName = 'MATLAB Kernel') => ({
    sessionContext: {
        ready: Promise.resolve(),
        kernelDisplayName,
        session: null,
        initialize: jest.fn(),
        isReady: true,
        isTerminating: false,
        // Add other required methods as
        dispose: jest.fn()
    },
    toolbar: {
        insertItem: jest.fn(),
        names: []
    // addItem: jest.fn(),
    // insertAfter: jest.fn(),
    // insertBefore: jest.fn()
    }
});

// Mock for ToolbarButton
const createMockToolbarButton = () => ({
    className: 'openMATLABButton',
    icon: matlabIcon,
    label: 'Open MATLAB',
    tooltip: 'Open MATLAB',
    onClick: expect.any(Function),
    dispose: jest.fn()
});

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
        test('should insert button when kernel is MATLAB Kernel', async () => {
            // Arrange
            const panel = createMockNotebookPanel('MATLAB Kernel');
            const button = createMockToolbarButton();

            // Act
            await insertButton(panel as unknown as NotebookPanel, button as any);

            // Assert
            expect(panel.toolbar!.insertItem).toHaveBeenCalledWith(
                10,
                'matlabToolbarButton',
                button
            );
        });

        test('should not insert button when kernel is not MATLAB Kernel', async () => {
            // Arrange
            const panel = createMockNotebookPanel('Python 3');
            const button = createMockToolbarButton();

            // Act
            await insertButton(panel as unknown as NotebookPanel, button as any);

            // Assert
            expect(panel.toolbar!.insertItem).not.toHaveBeenCalled();
        });

        test('should wait for session context to be ready before checking kernel', async () => {
            // Arrange
            const readyPromise = new Promise<void>((resolve) =>
                setTimeout(resolve, 10)
            );
            const panel = {
                sessionContext: {
                    ready: readyPromise,
                    kernelDisplayName: 'MATLAB Kernel'
                },
                toolbar: {
                    insertItem: jest.fn()
                }
            };
            const button = createMockToolbarButton();

            // Act
            const insertPromise = insertButton(panel as any, button as any);

            // Assert - insertItem should not be called before ready resolves
            expect(panel.toolbar.insertItem).not.toHaveBeenCalled();

            // Wait for ready promise to resolve
            await insertPromise;

            // Now insertItem should have been called
            expect(panel.toolbar.insertItem).toHaveBeenCalledWith(
                10,
                'matlabToolbarButton',
                button
            );
        });
    });

    describe('MatlabToolbarButtonExtension', () => {
        let extension: MatlabToolbarButtonExtension;
        let panel: any;
        let context: any;

        beforeEach(() => {
            extension = new MatlabToolbarButtonExtension();
            panel = createMockNotebookPanel();
            context = {};
        });

        test('should create a toolbar button with correct properties', () => {
            // Act
            const result = extension.createNew(panel, context);

            // Assert
            expect(result).toEqual(
                expect.objectContaining({
                    className: 'openMATLABButton',
                    icon: matlabIcon,
                    label: 'Open MATLAB',
                    tooltip: 'Open MATLAB'
                })
            );
        });

        test('should return a disposable object', () => {
            // Act
            const result = extension.createNew(panel, context);

            // Assert
            expect(result.dispose).toBeDefined();
            expect(typeof result.dispose).toBe('function');
        });

        test('button onClick should open MATLAB in a new tab', () => {
            // Arrange
            const ToolbarButtonMock = jest.requireMock(
                '@jupyterlab/apputils'
            ).ToolbarButton;
            let capturedOnClick: () => void = () => {}; // Initialize with empty function

            // Capture the onClick handler when ToolbarButton is constructed
            ToolbarButtonMock.mockImplementationOnce((options: any) => {
                capturedOnClick = options.onClick;
                return {
                    ...options,
                    dispose: jest.fn()
                };
            });

            // Act
            extension.createNew(
        panel as unknown as NotebookPanel,
        context as unknown as DocumentRegistry.IContext<INotebookModel>
            );
            // Manually call the onClick handler
            capturedOnClick();

            // Assert
            expect(window.open).toHaveBeenCalledWith(
                'http://localhost:8888/matlab',
                '_blank'
            );
        });

        test('should call insertButton with panel and button', () => {
            // Arrange
            // Import the module using ES modules syntax for TypeScript compatibility
            const matlabButtonModule = require('../plugins/matlabToolbarButton');
            const spy = jest
                .spyOn(matlabButtonModule, 'insertButton')
                .mockImplementation(() => Promise.resolve());

            // Act
            const button = extension.createNew(
        panel as unknown as NotebookPanel,
        context as unknown as DocumentRegistry.IContext<INotebookModel>
            );

            // Assert
            expect(spy).toHaveBeenCalledWith(panel, button);

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
