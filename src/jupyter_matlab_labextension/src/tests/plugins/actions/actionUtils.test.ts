// Copyright 2026 The MathWorks, Inc.

import { isCommValid } from '../../../plugins/actions/actionUtils';
import { ICommunicationChannel } from '../../../plugins/matlabCommunication';

describe('actionUtils', () => {
    describe('isCommValid', () => {
        it('should return true when comm is valid and not disposed', () => {
            const mockComm = {
                commId: 'test-comm-id',
                targetName: 'matlab',
                isDisposed: false,
                send: jest.fn(),
                close: jest.fn(),
                open: jest.fn(),
                onMsg: null,
                onClose: null
            } as unknown as ICommunicationChannel;

            expect(isCommValid(mockComm)).toBe(true);
        });

        it('should return false and log error when comm is null', () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            expect(isCommValid(null as any)).toBe(false);
            expect(errorSpy).toHaveBeenCalledWith('Communication channel is not available');

            errorSpy.mockRestore();
        });

        it('should return false and log error when comm is undefined', () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();

            expect(isCommValid(undefined as any)).toBe(false);
            expect(errorSpy).toHaveBeenCalledWith('Communication channel is not available');

            errorSpy.mockRestore();
        });

        it('should return false and log error when comm is disposed', () => {
            const errorSpy = jest.spyOn(console, 'error').mockImplementation();
            const disposedComm = {
                commId: 'test-comm-id',
                targetName: 'matlab',
                isDisposed: true,
                send: jest.fn(),
                close: jest.fn(),
                open: jest.fn(),
                onMsg: null,
                onClose: null
            } as unknown as ICommunicationChannel;

            expect(isCommValid(disposedComm)).toBe(false);
            expect(errorSpy).toHaveBeenCalledWith('Communication channel is not available');

            errorSpy.mockRestore();
        });
    });
});
