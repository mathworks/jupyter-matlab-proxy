// Copyright 2026 The MathWorks, Inc.

import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';

export interface PendingRequest {
    promise: PromiseDelegate<ReadonlyJSONValue>;
    result: any;
}

const pendingRequests = new Map<string, PendingRequest>();

export function generateRequestId (actionType: string, commId: string): string {
    return actionType + '_' + commId;
}

export function getOrCreatePendingRequest (requestId: string): { pending: PendingRequest; isNew: boolean } {
    const existing = pendingRequests.get(requestId);
    if (existing) {
        return { pending: existing, isNew: false };
    }

    const pending: PendingRequest = {
        promise: new PromiseDelegate<ReadonlyJSONValue>(),
        result: null
    };
    pendingRequests.set(requestId, pending);
    return { pending, isNew: true };
}

export function getPendingRequest (requestId: string): PendingRequest | undefined {
    return pendingRequests.get(requestId);
}

export function removePendingRequest (requestId: string): void {
    pendingRequests.delete(requestId);
}
