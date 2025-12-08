// Copyright 2025 The MathWorks, Inc.

import path from 'path';
import { NotebookPanel } from '@jupyterlab/notebook';
import { PageConfig } from '@jupyterlab/coreutils';

/**
 * Tracks metadata and kernel state for the currently active Jupyter notebook panel.
 * Provides helpers to determine whether the notebook is a MATLAB notebook, whether
 * its kernel is busy, resolve the notebook's file path, and control the kernel.
 */
export class NotebookInfo {
    private _notebookName: string | undefined = undefined;
    private _isMatlabNotebook: boolean = false;
    private _isBusy: boolean = false;
    private _panel: NotebookPanel | null = null;

    /*
     * Whether the current notebook’s kernelspec indicates MATLAB.
     *
     * @returns True if the current notebook is a MATLAB notebook; otherwise false.
    */
    isMatlabNotebook (): boolean {
        return this._isMatlabNotebook;
    }

    /*
     * Whether the kernel is busy, but only for MATLAB notebooks.
     * If the current notebook is not MATLAB, returns false.
     *
     * @returns True if the notebook is MATLAB and the kernel is busy; otherwise false.
    */
    isBusy (): boolean {
        return this._isMatlabNotebook ? this._isBusy : false;
    }

    /*
     * Absolute path to the current notebook on the filesystem.
     *
     * Combines the Jupyter server root with the notebook's relative path.
     *
     * @returns The absolute file path if available; otherwise undefined.
    */
    getCurrentFilePath (): string | undefined {
        if (this._notebookName) {
            return path.join(PageConfig.getOption('serverRoot'), this._notebookName);
        } else {
            return undefined;
        }
    }

    /*
     * Waits until the associated kernel reaches the 'idle' status.
     *
     * @throws Error if no notebook panel has been set via update().
     * @returns A promise that resolves when the kernel status becomes 'idle'.
    */
    async waitForIdleStatus (): Promise<void> {
        if (!this._panel) {
            throw Error('No notebook panel provided');
        } else {
            return new Promise((resolve) => {
                if (this._panel!.sessionContext.session?.kernel?.status === 'idle') {
                    resolve();
                } else {
                    const onStatusChanged = (connection: any, status: string) => {
                        if (status === 'idle') {
                            // Disconnect listener from statusChanged signal so that it doesn't get called again.
                            connection.statusChanged.disconnect(onStatusChanged);
                            resolve();
                        }
                    };
                    this._panel!.sessionContext.session?.kernel?.statusChanged.connect(
                        onStatusChanged
                    );
                }
            });
        }
    }

    /*
     * Updates the tracked notebook panel and refreshes its derived state:
     * - whether it is a MATLAB notebook (via kernelspec metadata),
     * - whether the kernel is currently busy,
     * - the notebook’s path.
     *
     * If panel is null, clears all tracked state.
     *
     * Note: Waits for the session context to be ready before reading kernel status.
     *
     * @param panel The active NotebookPanel to track, or null to reset.
     * @returns A promise that resolves when the state has been updated.
    */
    async update (panel: NotebookPanel | null): Promise<void> {
        if (panel) {
            // Wait for session context to be ready
            if (!panel.sessionContext.isReady) {
                await panel.sessionContext.ready;
            }
            this._panel = panel;
            this._isMatlabNotebook = panel.sessionContext.kernelDisplayName === 'MATLAB Kernel';
            const context = panel.context;
            this._isBusy = panel.sessionContext.session?.kernel?.status === 'busy';
            this._notebookName = context.path;
        } else {
            this._notebookName = undefined;
            this._isMatlabNotebook = false;
            this._isBusy = false;
            this._panel = null;
        }
    }

    /*
     * Sends an interrupt to the associated kernel, if available.
     * No-op if there is no tracked panel/session/kernel.
    */
    interrupt (): void {
        if (this._panel) {
            this._panel.sessionContext.session?.kernel?.interrupt();
            console.log('Kernel interupted');
        }
    }

    /*
     * Returns the current notebook’s path relative to the server root.
     *
     * @returns The relative path (e.g., 'folder/notebook.ipynb') or undefined if none is set.
    */
    getCurrentFilename (): string | undefined {
        return this._notebookName;
    }
}
