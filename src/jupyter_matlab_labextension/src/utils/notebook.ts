// Copyright 2026 The MathWorks, Inc.

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
    private _targetURL: string | undefined = undefined;

    /*
     * Whether the current notebook’s kernelspec indicates MATLAB.
     *
     * @returns True if the current notebook is a MATLAB notebook; otherwise false.
    */
    isMatlabNotebook (): boolean {
        return this._isMatlabNotebook;
    }

    getTargetURL (): string | undefined {
        return this._targetURL;
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
            return path.join(this.getCurrentDirectory()!, this._notebookName);
        } else {
            return undefined;
        }
    }

    getCurrentDirectory (): string | undefined {
        return PageConfig.getOption('serverRoot');
    }

    getCurrentFileName (): string | undefined {
        return this._notebookName;
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

            // Update all properties based on the provided panel
            this._isMatlabNotebook = panel.sessionContext.kernelDisplayName === 'MATLAB Kernel';
            const context = panel.context;
            this._isBusy = panel.sessionContext.session?.kernel?.status === 'busy';
            this._notebookName = context.path;
            const kernelID = panel.sessionContext.session?.kernel?.id;
            this._targetURL = PageConfig.getBaseUrl() + 'matlab/' + kernelID + '/';
        } else {
            this._notebookName = undefined;
            this._isMatlabNotebook = false;
            this._isBusy = false;
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
