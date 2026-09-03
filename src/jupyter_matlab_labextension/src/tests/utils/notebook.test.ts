// Copyright 2026 The MathWorks, Inc.

import { NotebookInfo } from '../../utils/notebook';
import { PageConfig } from '@jupyterlab/coreutils';

// --------------------
// Mocks
// --------------------
jest.mock('@jupyterlab/coreutils', () => ({
    PageConfig: {
        getOption: jest.fn(),
        getBaseUrl: jest.fn()
    }
}));

const mockedGetOption = PageConfig.getOption as jest.MockedFunction<typeof PageConfig.getOption>;
const mockedGetBaseUrl = PageConfig.getBaseUrl as jest.MockedFunction<typeof PageConfig.getBaseUrl>;

// ------------------------------
// Test Suite
// ------------------------------
describe('NotebookInfo', () => {
    let notebookInfo: NotebookInfo;

    beforeEach(() => {
        jest.clearAllMocks();
        notebookInfo = new NotebookInfo();
    });

    describe('initial state checks', () => {
        it('isMatlabNotebook returns false initially', () => {
            expect(notebookInfo.isMatlabNotebook()).toBe(false);
        });

        it('isBusy returns false initially', () => {
            expect(notebookInfo.isBusy()).toBe(false);
        });

        it('getCurrentFilePath returns undefined initially', () => {
            expect(notebookInfo.getCurrentFilePath()).toBeUndefined();
        });

        it('getCurrentFilename returns undefined initially', () => {
            expect(notebookInfo.getCurrentFilename()).toBeUndefined();
        });

        it('getTargetURL returns undefined initially', () => {
            expect(notebookInfo.getTargetURL()).toBeUndefined();
        });
    });

    describe('update with MATLAB notebook panel', () => {
        let panel: any;

        beforeEach(() => {
            panel = {
                context: { path: 'notebooks/test.ipynb' },
                sessionContext: {
                    isReady: true,
                    ready: Promise.resolve(),
                    kernelDisplayName: 'MATLAB Kernel',
                    session: {
                        kernel: {
                            id: 'kernel-123',
                            status: 'idle'
                        }
                    }
                }
            };
            mockedGetBaseUrl.mockReturnValue('http://localhost:8888/');
            mockedGetOption.mockReturnValue('/home/user');
        });

        it('sets isMatlabNotebook to true for MATLAB Kernel', async () => {
            await notebookInfo.update(panel);
            expect(notebookInfo.isMatlabNotebook()).toBe(true);
        });

        it('sets isBusy to false when kernel is idle', async () => {
            await notebookInfo.update(panel);
            expect(notebookInfo.isBusy()).toBe(false);
        });

        it('sets isBusy to true when kernel is busy', async () => {
            panel.sessionContext.session.kernel.status = 'busy';
            await notebookInfo.update(panel);
            expect(notebookInfo.isBusy()).toBe(true);
        });

        it('returns correct getCurrentFilename', async () => {
            await notebookInfo.update(panel);
            expect(notebookInfo.getCurrentFilename()).toBe('notebooks/test.ipynb');
        });

        it('returns correct getCurrentFileName', async () => {
            await notebookInfo.update(panel);
            expect(notebookInfo.getCurrentFileName()).toBe('notebooks/test.ipynb');
        });

        it('returns correct getCurrentFilePath', async () => {
            await notebookInfo.update(panel);
            expect(notebookInfo.getCurrentFilePath()).toBe('/home/user/notebooks/test.ipynb');
        });

        it('returns correct targetURL with kernel id', async () => {
            await notebookInfo.update(panel);
            expect(notebookInfo.getTargetURL()).toBe('http://localhost:8888/matlab/kernel-123/');
        });

        it('waits for session context to be ready if not ready', async () => {
            let resolveReady: () => void;
            const readyPromise = new Promise<void>((resolve) => {
                resolveReady = resolve;
            });
            panel.sessionContext.isReady = false;
            panel.sessionContext.ready = readyPromise;

            const updatePromise = notebookInfo.update(panel);

            // Resolve the ready promise
            resolveReady!();
            await updatePromise;

            expect(notebookInfo.isMatlabNotebook()).toBe(true);
        });
    });

    describe('update with non-MATLAB notebook panel', () => {
        let panel: any;

        beforeEach(() => {
            panel = {
                context: { path: 'notebooks/python.ipynb' },
                sessionContext: {
                    isReady: true,
                    ready: Promise.resolve(),
                    kernelDisplayName: 'Python 3',
                    session: {
                        kernel: {
                            id: 'python-kernel-456',
                            status: 'busy'
                        }
                    }
                }
            };
            mockedGetBaseUrl.mockReturnValue('http://localhost:8888/');
        });

        it('sets isMatlabNotebook to false for non-MATLAB kernel', async () => {
            await notebookInfo.update(panel);
            expect(notebookInfo.isMatlabNotebook()).toBe(false);
        });

        it('isBusy returns false even when kernel is busy for non-MATLAB notebook', async () => {
            await notebookInfo.update(panel);
            expect(notebookInfo.isBusy()).toBe(false);
        });
    });

    describe('update with null panel', () => {
        it('resets all state when panel is null', async () => {
            const panel = {
                context: { path: 'notebooks/test.ipynb' },
                sessionContext: {
                    isReady: true,
                    ready: Promise.resolve(),
                    kernelDisplayName: 'MATLAB Kernel',
                    session: {
                        kernel: {
                            id: 'kernel-123',
                            status: 'busy'
                        }
                    }
                }
            };
            mockedGetBaseUrl.mockReturnValue('http://localhost:8888/');

            await notebookInfo.update(panel as any);
            expect(notebookInfo.isMatlabNotebook()).toBe(true);

            await notebookInfo.update(null);

            expect(notebookInfo.isMatlabNotebook()).toBe(false);
            expect(notebookInfo.isBusy()).toBe(false);
            expect(notebookInfo.getCurrentFilename()).toBeUndefined();
            expect(notebookInfo.getCurrentFilePath()).toBeUndefined();
        });
    });
});
