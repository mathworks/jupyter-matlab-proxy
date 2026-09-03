// Copyright 2025-2026 The MathWorks, Inc.

// Mock dependencies from JupyterLab and other modules
import {
    MatlabCommunicationExtension,
    matlabCommPlugin,
    IMatlabCommunication
} from '../../plugins/matlabCommunication';
import { NotebookPanel } from '@jupyterlab/notebook';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { ActionFactory } from '../../plugins/actions/actionFactory';
import { NotebookInfo } from '../../utils/notebook';

jest.mock('@jupyterlab/services', () => ({
    KernelMessage: {
        createMessage: jest.fn()
    }
}));

jest.mock('@jupyterlab/notebook', () => ({
    NotebookPanel: jest.fn()
}));

jest.mock('../../utils/notebook', () => ({
    NotebookInfo: jest.fn().mockImplementation(() => ({
        update: jest.fn(),
        isMatlabNotebook: jest.fn(() => true)
    }))
}));

jest.mock('../../plugins/actions/actionFactory', () => ({
    ActionFactory: {
        createAction: jest.fn().mockReturnValue({
            onMsg: jest.fn()
        })
    }
}));

// Helper function to create mock comm
const createMockComm = (id: string = 'test-comm-id') => ({
    commId: id,
    targetName: 'matlab',
    onMsg: jest.fn(),
    onClose: jest.fn(),
    open: () => ({
        done: Promise.resolve()
    }),
    close: jest.fn(),
    isDisposed: false,
    dispose: jest.fn(),
    send: jest.fn()
});

const flushAsync = async (): Promise<void> => {
    await Promise.resolve();
    await Promise.resolve();
};

const mockNotebookType = (isMatlabNotebook: boolean): void => {
    const notebookInfoMock = NotebookInfo as unknown as jest.Mock;
    notebookInfoMock.mockImplementation(() => ({
        update: jest.fn(),
        isMatlabNotebook: jest.fn(() => isMatlabNotebook)
    }));
};

const createDeferred = (): {
    promise: Promise<void>;
    resolve: () => void;
} => {
    let resolve!: () => void;
    const promise = new Promise<void>((_resolve) => {
        resolve = _resolve;
    });
    return { promise, resolve };
};

// Begin testing MatlabCommunicationExtension
describe('MatlabCommunicationExtension', () => {
    let panel: NotebookPanel;
    let context: DocumentRegistry.IContext<any>;
    let extension: MatlabCommunicationExtension;
    let consoleLogSpy: jest.SpyInstance;
    let consoleErrorSpy: jest.SpyInstance;
    let consoleDebugSpy: jest.SpyInstance;

    beforeEach(() => {
        // Spy on console methods
        consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
        consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        consoleDebugSpy = jest.spyOn(console, 'debug').mockImplementation();
        mockNotebookType(true);

        // Mock NotebookPanel and context
        panel = {
            id: 'notebook-1',
            sessionContext: {
                ready: Promise.resolve(),
                session: {
                    kernel: {
                        id: 'kernel-1',
                        createComm: jest.fn(() => createMockComm('test-comm-id'))
                    }
                },
                kernelChanged: {
                    connect: jest.fn(),
                    disconnect: jest.fn()
                }
            },
            disposed: {
                connect: jest.fn()
            },
            isDisposed: false
        } as unknown as NotebookPanel;

        context = {} as DocumentRegistry.IContext<any>;

        extension = new MatlabCommunicationExtension();
    });

    afterEach(() => {
        jest.useRealTimers();
        consoleLogSpy.mockRestore();
        consoleErrorSpy.mockRestore();
        consoleDebugSpy.mockRestore();
    });

    describe('createNew', () => {
        it('should create a new communication channel for MATLAB notebooks', async () => {
            const disposable = extension.createNew(panel, context);

            // Wait for async operations to complete
            await panel.sessionContext.ready;

            const { kernel } = panel.sessionContext.session!;

            // Wait a bit more to ensure the async then block has executed
            await flushAsync();

            expect(kernel?.createComm).toHaveBeenCalled();
            expect(disposable.dispose).toBeDefined();
        });

        it('should not create a communication channel for non-MATLAB notebooks', async () => {
            mockNotebookType(false);

            const disposable = extension.createNew(panel, context);

            await panel.sessionContext.ready;

            // Ensure no channel is created
            expect(
                panel.sessionContext.session!.kernel!.createComm
            ).not.toHaveBeenCalled();
            expect(disposable.dispose).toBeDefined();
        });

        it('should log error when kernel is not ready', async () => {
            const panelWithNoKernel = {
                ...panel,
                sessionContext: {
                    ...panel.sessionContext,
                    session: null,
                    ready: Promise.resolve()
                }
            } as unknown as NotebookPanel;

            extension.createNew(panelWithNoKernel, context);
            await panelWithNoKernel.sessionContext.ready;
            await flushAsync();

            expect(consoleErrorSpy).toHaveBeenCalledWith(
                "Kernel not ready! Can't create communication channel"
            );
        });

        it('should handle sessionContext.ready rejection gracefully', async () => {
            const panelWithError = {
                ...panel,
                sessionContext: {
                    ...panel.sessionContext,
                    ready: Promise.reject(new Error('Session failed'))
                }
            } as unknown as NotebookPanel;

            extension.createNew(panelWithError, context);

            await flushAsync();

            expect(consoleErrorSpy).toHaveBeenCalledWith(
                'Notebook panel was not ready',
                expect.any(Error)
            );
        });

        it('should not connect or create comm if disposed before ready resolves', async () => {
            const deferredReady = createDeferred();
            const panelWithDeferredReady = {
                ...panel,
                sessionContext: {
                    ...panel.sessionContext,
                    ready: deferredReady.promise
                }
            } as unknown as NotebookPanel;

            const disposable = extension.createNew(panelWithDeferredReady, context);
            disposable.dispose();
            deferredReady.resolve();
            await flushAsync();

            const kernelChanged = panelWithDeferredReady.sessionContext.kernelChanged;
            expect(kernelChanged.connect).not.toHaveBeenCalled();
            expect(
                panelWithDeferredReady.sessionContext.session!.kernel!.createComm
            ).not.toHaveBeenCalled();
        });
    });

    describe('getComm', () => {
        it('should return the communication channel for a valid notebook ID', async () => {
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const comm = extension.getComm(panel.id);
            expect(comm).toBeDefined();
            expect(comm.commId).toBe('test-comm-id');
        });

        it('should throw an error if getComm is called with an invalid notebook ID', async () => {
            // First, create a communication channel for a valid notebook
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            // Verify that the valid notebook ID works (doesn't throw)
            expect(() => extension.getComm(panel.id)).not.toThrow();

            // Now test that an invalid ID throws the expected error
            expect(() => extension.getComm('invalid-id')).toThrowError(
                'No communication channel found for notebook ID: invalid-id'
            );
        });

        it('should throw an error if the comm is disposed', async () => {
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            // Get the comm and dispose it
            const comm = extension.getComm(panel.id);
            (comm as any).isDisposed = true;

            expect(() => extension.getComm(panel.id)).toThrowError(
                `No communication channel found for notebook ID: ${panel.id}`
            );
        });
    });

    describe('deleteComms', () => {
        it('should delete all communication channels during cleanup', async () => {
            // First create a communication channel
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            // Verify the comm exists
            expect(() => extension.getComm(panel.id)).not.toThrow();

            // Delete all comms
            extension.deleteComms();

            // Now it should throw
            expect(() => extension.getComm(panel.id)).toThrowError(
                `No communication channel found for notebook ID: ${panel.id}`
            );
        });

        it('should handle deleteComms when no comms exist', () => {
            // Should not throw when no comms exist
            expect(() => extension.deleteComms()).not.toThrow();
        });
    });

    describe('dispose and cleanup', () => {
        it('should clean up communication channels when the panel is disposed', async () => {
            const disposable = extension.createNew(panel, context);

            await panel.sessionContext.ready;
            await flushAsync();

            // Verify a comm was created
            const { kernel } = panel.sessionContext.session!;
            expect(kernel?.createComm).toHaveBeenCalled();

            // Comm should exist before disposal
            expect(() => extension.getComm(panel.id)).not.toThrow();

            // Simulate disposal via DisposableDelegate
            disposable.dispose();

            // Comm should now be cleaned up
            expect(() => extension.getComm(panel.id)).toThrow();
        });

        it('should disconnect kernelChanged handler on disposal', async () => {
            const disconnectSpy = jest.spyOn(
                panel.sessionContext.kernelChanged,
                'disconnect'
            );

            const disposable = extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            // Verify connect was called
            expect(panel.sessionContext.kernelChanged.connect).toHaveBeenCalled();

            // Dispose
            disposable.dispose();

            // Verify disconnect was called
            expect(disconnectSpy).toHaveBeenCalled();
        });
    });

    describe('_createAndOpenCommWithRetry', () => {
        it('should succeed on first attempt', async () => {
            const kernel = panel.sessionContext.session!.kernel!;
            const comm = await (extension as any)._createAndOpenCommWithRetry(
                kernel,
                'test-channel'
            );

            expect(comm).not.toBeNull();
            expect(kernel.createComm).toHaveBeenCalledWith('test-channel');
            expect(consoleLogSpy).toHaveBeenCalledWith(
                'Communication channel opened successfully with ID:',
                'test-comm-id'
            );
        });

        it('should retry on failure and eventually succeed', async () => {
            const kernel = panel.sessionContext.session!.kernel!;
            let attemptCount = 0;

            // Mock createComm to fail twice then succeed
            const mockCreateComm = jest.fn(() => {
                attemptCount++;
                if (attemptCount < 3) {
                    return {
                        ...createMockComm(`test-comm-id-${attemptCount}`),
                        open: () => ({
                            done: Promise.reject(new Error('Connection failed'))
                        })
                    };
                }
                return createMockComm('test-comm-id-success');
            });
            kernel.createComm = mockCreateComm as any;

            const comm = await (extension as any)._createAndOpenCommWithRetry(
                kernel,
                'test-channel'
            );

            expect(comm).not.toBeNull();
            expect(comm.commId).toBe('test-comm-id-success');
            expect(mockCreateComm).toHaveBeenCalledTimes(3);
        });

        it('should fail after max retries and return null', async () => {
            jest.useFakeTimers({ doNotFake: ['nextTick', 'setImmediate'] });
            const kernel = panel.sessionContext.session!.kernel!;

            // Mock createComm to always fail
            const mockCreateComm = jest.fn(() => ({
                ...createMockComm('test-comm-id'),
                open: () => ({
                    done: Promise.reject(new Error('Connection failed'))
                })
            }));
            kernel.createComm = mockCreateComm as any;

            const promise = (extension as any)._createAndOpenCommWithRetry(
                kernel,
                'test-channel'
            );

            // Advance through all retry delays
            await jest.advanceTimersByTimeAsync(200);
            await jest.advanceTimersByTimeAsync(400);
            await jest.advanceTimersByTimeAsync(800);
            await jest.advanceTimersByTimeAsync(1600);
            await jest.advanceTimersByTimeAsync(3200);

            const comm = await promise;

            expect(comm).toBeNull();
            expect(mockCreateComm).toHaveBeenCalledTimes(5); // maxRetries
            expect(consoleErrorSpy).toHaveBeenCalledWith(
                expect.stringContaining('Failed to create communication channel')
            );
        });

        it('should dispose failed comm attempts', async () => {
            jest.useFakeTimers({ doNotFake: ['nextTick', 'setImmediate'] });
            const kernel = panel.sessionContext.session!.kernel!;
            const disposeMock = jest.fn();

            const mockCreateComm = jest.fn(() => ({
                ...createMockComm('test-comm-id'),
                open: () => ({
                    done: Promise.reject(new Error('Connection failed'))
                }),
                dispose: disposeMock
            }));
            kernel.createComm = mockCreateComm as any;

            const promise = (extension as any)._createAndOpenCommWithRetry(
                kernel,
                'test-channel'
            );

            // Advance through all retry delays
            await jest.advanceTimersByTimeAsync(200);
            await jest.advanceTimersByTimeAsync(400);
            await jest.advanceTimersByTimeAsync(800);
            await jest.advanceTimersByTimeAsync(1600);
            await jest.advanceTimersByTimeAsync(3200);

            await promise;

            expect(disposeMock).toHaveBeenCalledTimes(5);
        });
    });

    describe('_openCommForPanel', () => {
        it('should skip recreation when valid comm exists for same kernel', async () => {
            // First call to create comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const kernel = panel.sessionContext.session!.kernel!;
            const createCommCallCount = (kernel.createComm as jest.Mock).mock.calls.length;

            // Second call should skip creation
            await (extension as any)._openCommForPanel(
                panel,
                panel.sessionContext.session!.kernel!
            );

            // createComm should not be called again
            expect((kernel.createComm as jest.Mock).mock.calls.length).toBe(createCommCallCount);
        });

        it('should dispose old comm before creating new one for different kernel', async () => {
            // First create a comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const oldComm = extension.getComm(panel.id);
            const oldCommCloseSpy = jest.spyOn(oldComm, 'close');

            // Change kernel and create new comm
            const newKernel = {
                id: 'kernel-2',
                createComm: jest.fn(() => createMockComm('new-comm-id'))
            };

            // Update panel's kernel
            (panel as any).sessionContext.session.kernel = newKernel;
            (panel as any).sessionContext.session.kernel.id = 'kernel-2';

            await (extension as any)._openCommForPanel(panel, newKernel as any);

            // Old comm should be disposed
            expect(oldCommCloseSpy).toHaveBeenCalled();
        });

        it('should handle race condition when panel is disposed during comm creation', async () => {
            const kernel = panel.sessionContext.session!.kernel!;
            const deferred = createDeferred();

            // Mock createComm with delay
            const mockCreateComm = jest.fn(() => ({
                ...createMockComm('test-comm-id'),
                open: () => ({
                    done: deferred.promise
                })
            }));
            kernel.createComm = mockCreateComm as any;

            const openPromise = (extension as any)._openCommForPanel(panel, kernel);

            // Mark panel as disposed during creation
            (panel as any).isDisposed = true;
            deferred.resolve();

            await openPromise;

            // Should not throw, but comm should not be stored
            expect(() => extension.getComm(panel.id)).toThrow();
        });

        it('should handle race condition when kernel changes during comm creation', async () => {
            const kernel = panel.sessionContext.session!.kernel!;
            const deferred = createDeferred();

            // Mock createComm with delay
            const mockCreateComm = jest.fn(() => ({
                ...createMockComm('test-comm-id'),
                open: () => ({
                    done: deferred.promise
                })
            }));
            kernel.createComm = mockCreateComm as any;

            const openPromise = (extension as any)._openCommForPanel(panel, kernel);

            // Change kernel ID during creation
            (panel as any).sessionContext.session.kernel.id = 'different-kernel-id';
            deferred.resolve();

            await openPromise;

            // Comm should be disposed due to kernel mismatch
            expect(() => extension.getComm(panel.id)).toThrow();
        });
    });

    describe('_handleKernelChange', () => {
        it('should dispose comm when panel is disposed', async () => {
            // First create a comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            // Mark panel as disposed
            (panel as any).isDisposed = true;

            // Trigger kernel change
            await (extension as any)._handleKernelChange(panel);

            // Comm should be cleaned up
            expect(() => extension.getComm(panel.id)).toThrow();
        });

        it('should dispose comm when no kernel is available', async () => {
            // First create a comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            // Remove kernel
            (panel as any).sessionContext.session.kernel = null;

            // Trigger kernel change
            await (extension as any)._handleKernelChange(panel);

            // Comm should be cleaned up
            expect(() => extension.getComm(panel.id)).toThrow();
        });

        it('should create new comm for new kernel', async () => {
            // First create initial comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const newKernel = {
                id: 'kernel-2',
                createComm: jest.fn(() => createMockComm('new-comm-id'))
            };

            // Update panel with new kernel
            (panel as any).sessionContext.session.kernel = newKernel;

            // Trigger kernel change
            await (extension as any)._handleKernelChange(panel);

            // New comm should exist
            const comm = extension.getComm(panel.id);
            expect(comm.commId).toBe('new-comm-id');
        });
    });

    describe('_configureComm', () => {
        it('should set up onMsg handler that routes to ActionFactory', async () => {
            const mockComm = createMockComm('test-comm-id');

            (extension as any)._configureComm(panel, mockComm as any);

            // Simulate receiving a message
            const testData = { action: 'test-action', data: { key: 'value' } };
            const testMsg = {
                content: {
                    data: testData
                }
            };

            // Call the onMsg handler
            mockComm.onMsg(testMsg as any);

            expect(ActionFactory.createAction).toHaveBeenCalledWith('test-action', false);
        });

        it('should ignore malformed message payloads', () => {
            const mockComm = createMockComm('test-comm-id');

            (extension as any)._configureComm(panel, mockComm as any);
            mockComm.onMsg({ content: { data: { invalid: true } } } as any);

            expect(ActionFactory.createAction).not.toHaveBeenCalled();
            expect(consoleErrorSpy).toHaveBeenCalledWith(
                'Malformed comm message received (missing action)',
                { invalid: true }
            );
        });

        it('should set up onClose handler that removes comm from map', async () => {
            // First create a comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const comm = extension.getComm(panel.id);

            // Store reference to onClose handler
            let onCloseHandler: Function | undefined;
            const originalOnClose = jest.fn();
            Object.defineProperty(comm, 'onClose', {
                set: (handler) => {
                    onCloseHandler = handler;
                },
                get: () => originalOnClose
            });

            // Re-configure to set up the handler
            (extension as any)._configureComm(panel, comm as any);

            // Comm should exist
            expect(() => extension.getComm(panel.id)).not.toThrow();

            // Call the onClose handler if it was set
            if (onCloseHandler) {
                onCloseHandler({});
            }
            expect(() => extension.getComm(panel.id)).toThrow();
        });
    });

    describe('_disposeCommForPanel', () => {
        it('should remove comm from map and dispose resources', async () => {
            // First create a comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const comm = extension.getComm(panel.id);
            const closeSpy = jest.spyOn(comm, 'close');

            // Dispose the comm
            (extension as any)._disposeCommForPanel(panel.id);

            // Comm should be removed from map
            expect(() => extension.getComm(panel.id)).toThrow();

            // Resources should be disposed
            expect(closeSpy).toHaveBeenCalled();
        });

        it('should handle already disposed comm gracefully', async () => {
            // First create a comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const comm = extension.getComm(panel.id);
            (comm as any).isDisposed = true;

            // Should not throw
            expect(() =>
                (extension as any)._disposeCommForPanel(panel.id)
            ).not.toThrow();
        });

        it('should do nothing when panel has no comm', () => {
            // Should not throw when panel has no comm
            expect(() =>
                (extension as any)._disposeCommForPanel('non-existent-panel')
            ).not.toThrow();
        });
    });

    describe('_removeCommForPanel', () => {
        it('should remove comm when it matches', async () => {
            // First create a comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const comm = extension.getComm(panel.id);

            // Remove the comm
            (extension as any)._removeCommForPanel(panel.id, comm as any);

            // Comm should be removed
            expect(() => extension.getComm(panel.id)).toThrow();
        });

        it('should skip removal when comm does not match', async () => {
            // First create a comm
            extension.createNew(panel, context);
            await panel.sessionContext.ready;
            await flushAsync();

            const differentComm = {
                commId: 'different-comm-id',
                targetName: 'different-target',
                isDisposed: false
            };

            // Try to remove with different comm
            (extension as any)._removeCommForPanel(panel.id, differentComm as any);

            // Original comm should still exist
            expect(() => extension.getComm(panel.id)).not.toThrow();
        });

        it('should do nothing when panel has no comm', () => {
            // Should not throw when panel has no comm
            expect(() =>
                (extension as any)._removeCommForPanel('non-existent-panel')
            ).not.toThrow();
        });
    });
});

describe('matlabCommPlugin', () => {
    it('should have correct id and autoStart properties', () => {
        expect(matlabCommPlugin.id).toBe('@mathworks/matlabCommPlugin');
        expect(matlabCommPlugin.autoStart).toBe(true);
    });

    it('should require INotebookTracker', () => {
        expect(matlabCommPlugin.requires).toBeDefined();
        expect(matlabCommPlugin.requires!.length).toBe(1);
    });

    it('should provide IMatlabCommunication token', () => {
        expect(matlabCommPlugin.provides).toBe(IMatlabCommunication);
    });

    it('should add extension to docRegistry on activation', () => {
        const mockApp = {
            docRegistry: {
                addWidgetExtension: jest.fn()
            }
        } as unknown as JupyterFrontEnd;

        const mockNotebookTracker = {} as any;

        matlabCommPlugin.activate!(mockApp, mockNotebookTracker);

        expect(mockApp.docRegistry.addWidgetExtension).toHaveBeenCalledWith(
            'Notebook',
            expect.any(MatlabCommunicationExtension)
        );
    });

    it('should set up beforeunload listener on activation', () => {
        const addEventListenerSpy = jest.spyOn(window, 'addEventListener');

        const mockApp = {
            docRegistry: {
                addWidgetExtension: jest.fn()
            }
        } as unknown as JupyterFrontEnd;

        const mockNotebookTracker = {} as any;

        matlabCommPlugin.activate!(mockApp, mockNotebookTracker);

        expect(addEventListenerSpy).toHaveBeenCalledWith(
            'beforeunload',
            expect.any(Function)
        );

        addEventListenerSpy.mockRestore();
    });
});
