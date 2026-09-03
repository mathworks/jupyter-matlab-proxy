// Copyright 2026 The MathWorks, Inc.

import { ICommunicationChannel } from '../matlabCommunication';

/**
 * Validates that a communication channel is available and not disposed.
 * @param comm The communication channel to validate
 * @returns true if the channel is valid, false otherwise
 */
export function isCommValid (comm: ICommunicationChannel): boolean {
    if (!comm || comm.isDisposed) {
        console.error('Communication channel is not available');
        return false;
    }
    return true;
}
