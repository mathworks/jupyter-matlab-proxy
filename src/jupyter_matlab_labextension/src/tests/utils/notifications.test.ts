// Copyright 2026 The MathWorks, Inc.

import {
    displayUserSigninNotification,
    displayStartingMatlabNotification,
    displayOpenMatlabNotification,
    displayUnsupportedMatlabVersionNotification,
    displayConversionNotification
} from '../../utils/notifications';
import { Notification } from '@jupyterlab/apputils';
import { PromiseDelegate } from '@lumino/coreutils';

jest.mock('@jupyterlab/apputils', () => ({
    Notification: {
        promise: jest.fn(),
        info: jest.fn(),
        error: jest.fn()
    }
}));

const mockedNotificationPromise = Notification.promise as jest.MockedFunction<typeof Notification.promise>;
const mockedNotificationInfo = Notification.info as jest.MockedFunction<typeof Notification.info>;
const mockedNotificationError = Notification.error as jest.MockedFunction<typeof Notification.error>;

describe('notifications module', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    describe('displayUserSigninNotification', () => {
        it('calls Notification.promise with correct pending, success, and error messages', async () => {
            const promise = displayUserSigninNotification();

            // Advance past the 1500ms sleep
            await jest.advanceTimersByTimeAsync(1500);
            const result = await promise;

            expect(mockedNotificationPromise).toHaveBeenCalledWith(
                expect.any(Promise),
                expect.objectContaining({
                    pending: expect.objectContaining({
                        message: 'Waiting for user to sign in to MATLAB.',
                        options: { autoClose: false }
                    }),
                    success: expect.objectContaining({
                        options: { autoClose: 3000 }
                    }),
                    error: expect.objectContaining({})
                })
            );

            expect(result).toBeInstanceOf(PromiseDelegate);
        });

        it('returns a PromiseDelegate that can be resolved', async () => {
            const promise = displayUserSigninNotification();
            await jest.advanceTimersByTimeAsync(1500);
            const delegate = await promise;

            expect(delegate.resolve).toBeDefined();
            expect(delegate.reject).toBeDefined();
        });
    });

    describe('displayStartingMatlabNotification', () => {
        it('calls Notification.promise with correct pending, success, and error messages', () => {
            const result = displayStartingMatlabNotification();

            expect(mockedNotificationPromise).toHaveBeenCalledWith(
                expect.any(Promise),
                expect.objectContaining({
                    pending: expect.objectContaining({
                        message: 'Starting MATLAB...',
                        options: { autoClose: false }
                    }),
                    success: expect.objectContaining({
                        options: { autoClose: 3000 }
                    }),
                    error: expect.objectContaining({})
                })
            );

            expect(result).toBeInstanceOf(PromiseDelegate);
        });

        it('returns a PromiseDelegate that can be resolved', () => {
            const delegate = displayStartingMatlabNotification();

            expect(delegate.resolve).toBeDefined();
            expect(delegate.reject).toBeDefined();
        });
    });

    describe('displayOpenMatlabNotification', () => {
        it('calls Notification.info with correct message and autoClose', () => {
            displayOpenMatlabNotification();

            expect(mockedNotificationInfo).toHaveBeenCalledWith(
                'Opening MATLAB...',
                { autoClose: 2000 }
            );
        });
    });

    describe('displayUnsupportedMatlabVersionNotification', () => {
        it('calls Notification.error with correct message and autoClose', () => {
            displayUnsupportedMatlabVersionNotification();

            expect(mockedNotificationError).toHaveBeenCalledWith(
                'Conversion to Live Script requires MATLAB R2025a or later.',
                { autoClose: 5000 }
            );
        });
    });

    describe('displayConversionNotification', () => {
        it('calls Notification.promise with correct pending, success, and error messages', () => {
            const result = displayConversionNotification();

            expect(mockedNotificationPromise).toHaveBeenCalledWith(
                expect.any(Promise),
                expect.objectContaining({
                    pending: expect.objectContaining({
                        message: 'Waiting for conversion to complete...',
                        options: { autoClose: false }
                    }),
                    success: expect.objectContaining({
                        options: { autoClose: 3000 }
                    }),
                    error: expect.objectContaining({})
                })
            );

            expect(result).toBeInstanceOf(PromiseDelegate);
        });

        it('returns a PromiseDelegate that can be resolved', () => {
            const delegate = displayConversionNotification();

            expect(delegate.resolve).toBeDefined();
            expect(delegate.reject).toBeDefined();
        });

        it('rejects the promise after default timeout', () => {
            const delegate = displayConversionNotification();
            // Catch the rejection to prevent unhandled promise rejection
            delegate.promise.catch(() => {});
            const rejectSpy = jest.spyOn(delegate, 'reject');

            jest.advanceTimersByTime(50000);

            expect(rejectSpy).toHaveBeenCalledWith({
                reason: 'Conversion process timed out'
            });
        });

        it('rejects the promise after custom timeout', () => {
            const delegate = displayConversionNotification(1000);
            delegate.promise.catch(() => {});
            const rejectSpy = jest.spyOn(delegate, 'reject');

            jest.advanceTimersByTime(1000);

            expect(rejectSpy).toHaveBeenCalledWith({
                reason: 'Conversion process timed out'
            });
        });

        it('does not reject before timeout', () => {
            const delegate = displayConversionNotification(5000);
            delegate.promise.catch(() => {});
            const rejectSpy = jest.spyOn(delegate, 'reject');

            jest.advanceTimersByTime(4999);

            expect(rejectSpy).not.toHaveBeenCalled();
        });
    });
});
