// Copyright 2025-2026 The MathWorks, Inc.

import {
    JupyterFrontEnd,
    JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { DocumentRegistry } from '@jupyterlab/docregistry';
import {
    INotebookModel,
    INotebookTracker,
    NotebookPanel
} from '@jupyterlab/notebook';
import { KernelMessage, Kernel } from '@jupyterlab/services';
import { JSONObject, JSONValue, Token } from '@lumino/coreutils';
import { DisposableDelegate } from '@lumino/disposable';
import { NotebookInfo } from '../utils/notebook';
import { ActionFactory } from './actions/actionFactory';

// Add more action types as needed
type CommunicationData = {
  action: string;
  data: JSONValue;
};

export interface ICommunicationChannel {
  readonly commId: string;
  readonly targetName: string;
  readonly isDisposed: boolean;
  onMsg: (msg: KernelMessage.ICommMsgMsg) => void | PromiseLike<void>;
  onClose: (msg: KernelMessage.ICommCloseMsg) => void | PromiseLike<void>;
  /**
   * Clean up the communication channel resources.
   * This is necessary to prevent memory leaks when channels are no longer needed.
   */
  dispose: () => void;
  close: (
    data?: JSONValue,
    metadata?: JSONObject,
    buffers?: (ArrayBuffer | ArrayBufferView)[]
  ) => void;
  send: (
    data: CommunicationData,
    metadata?: JSONObject,
    buffers?: (ArrayBuffer | ArrayBufferView)[],
    disposeOnDone?: boolean
  ) => void;
}
export interface ICommunicationService {
  getComm(notebookID: string): ICommunicationChannel;
}

/**
 * Tracks the communication state for a notebook panel.
 * We store both the comm channel and the kernel ID to detect when the kernel
 * has changed and avoid recreating comms unnecessarily for the same kernel.
 */
type CommunicationState = {
  comm: ICommunicationChannel;
  kernelId: string;
};

export class MatlabCommunicationExtension
implements
    DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel>,
    ICommunicationService {
    private _comms = new Map<string, CommunicationState>();
    private static readonly _maxOpenRetries = 5;
    private static readonly _initialRetryDelayInMS = 200;

    /*
     * Attempts to open a comm channel with a retry mechanism.
     * @param kernel The kernel for which a comm channel is being created.

     * @returns A promise that resolves when the comm is open.
    */
    private async _createAndOpenCommWithRetry (kernel: Kernel.IKernelConnection, channelName: string): Promise<Kernel.IComm | null> {
        let delayInMS = MatlabCommunicationExtension._initialRetryDelayInMS;
        let comm: Kernel.IComm | undefined;

        for (
            let attempt = 1;
            attempt <= MatlabCommunicationExtension._maxOpenRetries;
            attempt += 1
        ) {
            try {
                // Creates comm object on the client side
                comm = kernel.createComm(channelName);

                // Attempts to open a channel with the kernel
                await comm.open().done;
                console.log('Communication channel opened successfully with ID:', comm.commId);
                return comm;
            } catch (error) {
                console.error('Error opening communication channel', error);
                console.error(`Attempt #${attempt} failed. Waiting ${delayInMS}ms before next attempt.`);
                if (comm && !comm.isDisposed) {
                    comm.dispose();
                }
            }
            if (attempt < MatlabCommunicationExtension._maxOpenRetries) {
                // Wait for the delay before retrying.
                await new Promise(resolve => setTimeout(resolve, delayInMS));
                delayInMS *= 2;
            }
        }

        console.error(
            `Failed to create communication channel after ${MatlabCommunicationExtension._maxOpenRetries} attempts.`
        );
        return null;
    }

    private _extractCommunicationData (
        msg: KernelMessage.ICommMsgMsg
    ): CommunicationData | null {
        const data = msg.content.data as unknown;
        if (!data || typeof data !== 'object') {
            console.error('Malformed comm message received (non-object payload)', data);
            return null;
        }

        const action = (data as { action?: unknown }).action;
        if (typeof action !== 'string' || action.length === 0) {
            console.error('Malformed comm message received (missing action)', data);
            return null;
        }

        return data as CommunicationData;
    }

    /**
     * Removes the comm entry from the internal map for a given panel.
     * This is a lightweight operation that only removes the reference without
     * closing or disposing the actual comm channel. Used when the comm is already
     * closed externally (e.g., by the kernel) and we just need to clean up our map.
     *
     * @param panelId - The ID of the notebook panel
     * @param comm - Optional comm channel to validate against (ensures we don't remove
     *               the wrong comm if it was already replaced)
     */
    private _removeCommForPanel (panelId: string, comm?: ICommunicationChannel): void {
        const state = this._comms.get(panelId);
        if (!state) {
            return;
        }

        if (comm && state.comm !== comm) {
            return;
        }

        this._comms.delete(panelId);
    }

    /**
     * Properly disposes the comm channel for a given panel.
     * Unlike _removeCommForPanel, this method both removes the entry from the map
     * AND closes/disposes the actual comm channel to free up resources.
     * This prevents memory leaks and ensures clean shutdown of communication.
     *
     * @param panelId - The ID of the notebook panel whose comm should be disposed
     */
    private _disposeCommForPanel (panelId: string): void {
        const state = this._comms.get(panelId);
        if (!state) {
            return;
        }

        const { comm } = state;
        this._comms.delete(panelId);

        if (!comm.isDisposed) {
            try {
                comm.close();
            } catch (error) {
                console.debug('Error closing communication channel', error);
            }

            if (!comm.isDisposed) {
                comm.dispose();
            }
        }
    }

    /**
     * Configures message handlers for a communication channel.
     * Sets up callbacks for incoming messages and close events from the kernel.
     * This centralizes the comm configuration logic that was previously inline.
     *
     * @param panel - The notebook panel associated with this comm
     * @param comm - The communication channel to configure
     */
    private _configureComm (
        panel: NotebookPanel,
        comm: ICommunicationChannel
    ): void {
        comm.onMsg = (msg: KernelMessage.ICommMsgMsg) => {
            const data = this._extractCommunicationData(msg);
            if (!data) {
                return;
            }

            console.debug('Received data from kernel: ', data);
            const actionType = data.action;
            const action = ActionFactory.createAction(actionType, false);

            action.onMsg(data, comm);
        };

        comm.onClose = (msg) => {
            console.debug(`Received data:${msg} for comm close event.`);
            console.log(`Comm with ID:${comm.commId} closed.`);
            this._removeCommForPanel(panel.id, comm);
        };
    }

    /**
     * Opens a communication channel for a notebook panel with the given kernel.
     * This method handles kernel validation to avoid unnecessary comm recreation:
     * - If a valid comm already exists for this kernel, it returns early
     * - If the kernel has changed or no comm exists, it disposes the old one and creates new
     * - After async creation, it validates the panel/kernel are still valid before storing
     *
     * @param panel - The notebook panel to open comm for
     * @param kernel - The kernel connection to communicate with
     */
    private async _openCommForPanel (
        panel: NotebookPanel,
        kernel: Kernel.IKernelConnection
    ): Promise<void> {
        const kernelId = kernel.id ?? '';
        const existingState = this._comms.get(panel.id);
        // Optimization: Skip recreation if we already have a valid comm for this kernel
        if (
            existingState &&
            existingState.kernelId === kernelId &&
            !existingState.comm.isDisposed
        ) {
            return;
        }

        this._disposeCommForPanel(panel.id);

        const channelName = 'matlab_comm_' + panel.id;
        console.log('Attempting to establish communication with the kernel');

        const comm = await this._createAndOpenCommWithRetry(kernel, channelName);
        if (!comm) {
            return;
        }

        this._configureComm(panel, comm);

        // Race condition protection: After async operations, verify panel/kernel still valid
        // The panel might have been disposed or the kernel might have changed while we were waiting
        const currentKernelId = panel.sessionContext.session?.kernel?.id ?? '';
        if (panel.isDisposed || currentKernelId !== kernelId) {
            if (!comm.isDisposed) {
                comm.close();
                if (!comm.isDisposed) {
                    comm.dispose();
                }
            }
            return;
        }

        this._comms.set(panel.id, { comm, kernelId });
    }

    /**
     * Handles kernel change events for a notebook panel.
     * This is called whenever the kernel for a notebook changes (restart, new kernel, etc.).
     * It properly cleans up the old comm and establishes a new one with the new kernel.
     *
     * @param panel - The notebook panel whose kernel changed
     */
    private async _handleKernelChange (panel: NotebookPanel): Promise<void> {
        if (panel.isDisposed) {
            this._disposeCommForPanel(panel.id);
            return;
        }

        const kernel = panel.sessionContext.session?.kernel;
        if (!kernel) {
            this._disposeCommForPanel(panel.id);
            return;
        }

        await this._openCommForPanel(panel, kernel);
    }

    createNew (
        panel: NotebookPanel,
        _context: DocumentRegistry.IContext<INotebookModel>
    ): DisposableDelegate {
        /**
         * Track whether this panel's delegate has been disposed.
         * This flag prevents error logging for expected failures when the panel
         * is being cleaned up (e.g., user closed the notebook tab while comm was opening).
         */
        let disposed = false;

        /**
         * Handler for kernel change events. Using a named function allows us to
         * properly disconnect it during cleanup to prevent memory leaks.
         */
        const onKernelChanged = (): void => {
            this._handleKernelChange(panel).catch((error) => {
                console.error(
                    `Error handling kernel change for panel ${panel.id}:`,
                    error
                );
            });
        };

        panel.sessionContext.ready
            .then(async () => {
                if (disposed || panel.isDisposed) {
                    return;
                }

                const kernel = panel.sessionContext.session?.kernel;
                // If kernel is available, create channel and set up listeners.
                if (!kernel) {
                    console.error("Kernel not ready! Can't create communication channel");
                    return;
                }

                const notebookInfo = new NotebookInfo();
                await notebookInfo.update(panel);
                if (disposed || panel.isDisposed) {
                    return;
                }

                if (!notebookInfo.isMatlabNotebook()) {
                    console.debug('Not a MATLAB notebook, skipping communication setup');
                    return;
                }

                console.log('MATLAB Communication plugin activated for ', panel.id);
                // Connect to kernel change events so we can recreate comms when kernel restarts
                panel.sessionContext.kernelChanged.connect(onKernelChanged);

                try {
                    await this._openCommForPanel(panel, kernel);
                } catch (error) {
                    // Only log errors if the panel hasn't been disposed
                    // Prevents confusing error messages during normal cleanup
                    if (!disposed) {
                        console.error('Failed to create communication channel', error);
                    }
                }
            })
            .catch((error) => {
                console.error('Notebook panel was not ready', error);
            });

        return new DisposableDelegate(() => {
            disposed = true;
            // Disconnect the kernel change handler
            panel.sessionContext.kernelChanged.disconnect(onKernelChanged);
            // Clean up the comm channel for this panel
            this._disposeCommForPanel(panel.id);
        });
    }

    /**
     * Retrieves the communication channel for a notebook.
     * Validates that the channel exists and hasn't been disposed before returning.
     *
     * @param notebookId - The ID of the notebook
     * @returns The active communication channel
     * @throws Error if no active channel exists for the notebook
     */
    getComm (notebookId: string): ICommunicationChannel {
        const state = this._comms.get(notebookId);
        // Check both existence and disposal state to avoid returning dead channels
        if (!state || state.comm.isDisposed) {
            throw new Error(
                `No communication channel found for notebook ID: ${notebookId}`
            );
        }
        return state.comm;
    }

    /**
     * Disposes all communication channels.
     * Iterates through all tracked panels and properly closes/disposes their comms.
     * This is called when the page is being unloaded to prevent resource leaks.
     */
    deleteComms (): void {
        // Iterate through all tracked comms and dispose them properly
        // We use _disposeCommForPanel to ensure both map cleanup and resource disposal
        for (const panelId of this._comms.keys()) {
            this._disposeCommForPanel(panelId);
        }
    }
}

// A unique token for the comm service
export const IMatlabCommunication = new Token<ICommunicationService>('@mathworks/matlab-comm:IMatlabCommunication');

export const matlabCommPlugin: JupyterFrontEndPlugin<MatlabCommunicationExtension> =
  {
      id: '@mathworks/matlabCommPlugin',
      autoStart: true,
      requires: [INotebookTracker],
      provides: IMatlabCommunication,
      activate: (app: JupyterFrontEnd, _tracker: INotebookTracker): MatlabCommunicationExtension => {
          const matlabCommExtension = new MatlabCommunicationExtension();
          app.docRegistry.addWidgetExtension('Notebook', matlabCommExtension);

          // Dispose resources created by this plugin when the page unloads.
          // Need to handle this separately for the case when jupyterlab tab is closed directly
          window.addEventListener('beforeunload', () => {
              matlabCommExtension.deleteComms();
          });

          return matlabCommExtension;
      }
  };
