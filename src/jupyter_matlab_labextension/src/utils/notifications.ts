// Copyright 2026 The MathWorks, Inc.

import { PromiseDelegate, ReadonlyJSONValue } from '@lumino/coreutils';
import { Notification } from '@jupyterlab/apputils';

export async function displayUserSigninNotification () : Promise<PromiseDelegate<ReadonlyJSONValue>> {
    const userSigninPromise = new PromiseDelegate<ReadonlyJSONValue>();
    Notification.promise(userSigninPromise.promise, {
        pending: {
            message: ((): string => {
                return 'Waiting for user to sign in to MATLAB.';
            })(),
            options: { autoClose: false }
        },
        success: {
            message: (): string => {
                return 'Signed in successfully';
            },
            options: { autoClose: 3000 }
        },
        error: { message: () => 'Unable to sign in to MATLAB.' }
    });

    // Sleep for 1.5 seconds to allow the notification to render
    await new Promise((resolve) => setTimeout(resolve, 1500));

    return userSigninPromise;
}

export function displayStartingMatlabNotification () : PromiseDelegate<ReadonlyJSONValue> {
    const startingMatlabPromise = new PromiseDelegate<ReadonlyJSONValue>();
    Notification.promise(startingMatlabPromise.promise, {
        pending: {
            message: ((): string => {
                return 'Starting MATLAB...';
            })(),
            options: { autoClose: false }
        },
        success: {
            message: (): string => {
                return 'MATLAB is running.';
            },
            options: { autoClose: 3000 }
        },
        error: { message: () => 'Failed to start MATLAB' }
    });

    return startingMatlabPromise;
}

export function displayOpenMatlabNotification () : void {
    Notification.info('Opening MATLAB...', { autoClose: 2000 });
}

export function displayUnsupportedMatlabVersionNotification (): void {
    Notification.error(
        'Conversion to Live Script requires MATLAB R2025a or later.',
        { autoClose: 5000 }
    );
}

export function displayConversionNotification (
    timeoutInMS: number = 50000) : PromiseDelegate<ReadonlyJSONValue> {
    const conversionPromise = new PromiseDelegate<ReadonlyJSONValue>();

    setTimeout(() => {
        if (conversionPromise) {
            conversionPromise.reject({
                reason: 'Conversion process timed out'
            });
        }
    }, timeoutInMS);

    Notification.promise(conversionPromise.promise, {
        pending: {
            message: 'Waiting for conversion to complete...',
            options: { autoClose: false }
        },
        success: {
            message: (): string => {
                return 'Notebook converted successfully.';
            },
            options: { autoClose: 3000 }
        },
        error: { message: () => 'Unable to convert notebook.' }
    });

    return conversionPromise;
}
