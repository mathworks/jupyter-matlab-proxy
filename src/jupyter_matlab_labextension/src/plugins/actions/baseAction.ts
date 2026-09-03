// Copyright 2026 The MathWorks, Inc.

import { ICommunicationChannel } from '../matlabCommunication';

// Abstract Action class which other actions are meant to implement.

export abstract class BaseAction {
    /**
     * Whether {@link execute} should wait for the kernel's response before
     * resolving. When `true`, `execute` awaits an internal promise that is
     * settled by {@link onMsg} once the matching reply arrives; when `false`,
     * `execute` fires the request and returns without waiting.
     */
    protected blocking: boolean = false;

  /**
   * Sends this action's request to the kernel over the comm channel.
   *
   * Concrete actions validate `data`, send the request via `comm.send(...)`,
   * and — when {@link blocking} is `true` — wait for the kernel's reply
   * (delivered later through {@link onMsg}) before resolving.
   *
   * @param data - Action-specific payload to send to the kernel.
   * @param comm - Communication channel used to reach the kernel.
   */
  abstract execute(data: any, comm: ICommunicationChannel): void;

  /**
   * Handles a reply message received from the kernel for this action.
   *
   * Invoked by the comm layer's `onMsg` dispatcher when a message tagged with
   * this action type arrives. Implementations process the result (and, for
   * blocking actions, resolve or reject the promise awaited by
   * {@link execute}).
   *
   * @param data - Response payload sent by the kernel.
   * @param comm - Communication channel the message arrived on.
   */
  abstract onMsg(data: any, comm: ICommunicationChannel): void;

  /**
   * Returns the action type identifier for this action.
   *
   * Used to route requests and replies between the lab extension and the
   * kernel; the returned value is one of the {@link ActionTypes} constants.
   *
   * @returns The action type string.
   */
  abstract getActionName(): string;
}
