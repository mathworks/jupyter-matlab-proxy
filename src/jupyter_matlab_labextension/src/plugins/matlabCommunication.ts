// Copyright 2025 The MathWorks, Inc.

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

export class MatlabCommunicationExtension
implements
    DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel>,
    ICommunicationService {
    private _comms = new Map<string, ICommunicationChannel>();

    /*
     * Attempts to open a comm channel with a retry mechanism.
     * @param kernel The kernel for which a comm channel is being created.

     * @returns A promise that resolves when the comm is open.
    */
    private async _createAndOpenCommWithRetry (kernel: Kernel.IKernelConnection, channelName: string): Promise<Kernel.IComm | null> {
        let attempt = 1;
        let delayInMS = 200;
        const maxRetries = 5;

        while (attempt <= maxRetries) {
            try {
                // Creates comm object on the client side
                const comm = kernel.createComm(channelName);

                // Attempts to open a channel with the kernel
                await comm.open().done;
                console.log('Communication channel opened successfully with ID:', comm.commId);
                return comm;
            } catch (error) {
                console.error('Error opening communication channel', error);
                console.error(`Attempt #${attempt} failed. Waiting ${delayInMS}ms before next attempt.`);
            }
            // Wait for the delay
            await new Promise(resolve => setTimeout(resolve, delayInMS));

            // Update
            delayInMS *= 2;
            attempt += 1;
        }

        console.error(`Failed to create communication channel after ${attempt} attempts.`);
        return null;
    }

    createNew (
        panel: NotebookPanel,
        context: DocumentRegistry.IContext<INotebookModel>
    ): DisposableDelegate {
        panel.sessionContext.ready
            .then(async () => {
                const kernel = panel.sessionContext.session?.kernel;
                // If kernel is available, create channel and set up listeners.
                if (!kernel) {
                    console.error("Kernel not ready! Can't create communication channel");
                    return new DisposableDelegate(() => {});
                }

                const notebookInfo = new NotebookInfo();
                await notebookInfo.update(panel);

                if (!notebookInfo.isMatlabNotebook()) {
                    console.debug('Not a MATLAB notebook, skipping communication setup');
                    return new DisposableDelegate(() => {});
                }

                console.log('MATLAB Communication plugin activated for ', panel.id);

                // Create a unique channel name for this notebook
                const channelName = 'matlab_comm_' + panel.id;
                console.log(
                    'Attempting to establish communication with the kernel'
                );

                const comm = await this._createAndOpenCommWithRetry(kernel, channelName);
                if (!comm) {
                    return new DisposableDelegate(() => {});
                }

                // Listen for messages from the kernel
                comm.onMsg = (msg: KernelMessage.ICommMsgMsg) => {
                    const data = msg.content.data as CommunicationData;
                    console.debug('Recieved data from kernel: ', data);
                };

                // Handle comm close
                comm.onClose = (msg) => {
                    console.debug(`Received data:${msg} for comm close event.`);
                    console.log(`Comm with ID:${comm.commId} closed.`);
                };

                this._comms.set(panel.id, comm);
            })
            .catch((error) => {
                console.error('Notebook panel was not ready', error);
            });

        return new DisposableDelegate(() => {
            const comm = this._comms.get(panel.id);
            if (comm && !comm.isDisposed) {
                comm.close();
                this._comms.delete(panel.id);
            }
        });
    }

    getComm (notebookId: string): ICommunicationChannel {
        const commChannel = this._comms.get(notebookId);
        if (!commChannel) {
            throw new Error(
                `No communication channel found for notebook ID: ${notebookId}`
            );
        }
        return commChannel;
    }

    deleteComms (): void {
        this._comms.clear();
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
      activate: (app: JupyterFrontEnd): MatlabCommunicationExtension => {
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
