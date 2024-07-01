% Copyright 2024 The MathWorks, Inc.

classdef TestGetOrStashExceptionsFunction < matlab.unittest.TestCase
% TestCompleteFunction contains unit tests for the getOrStashExceptions function
    properties
        TestPaths
    end

    methods (TestClassSetup)
        function addFunctionPath(testCase)
            testCase.TestPaths = cellfun(@(relative_path)(fullfile(pwd, relative_path)), {"../../src/jupyter_matlab_kernel/matlab", "../../tests/matlab-tests/"}, 'UniformOutput', false);
            cellfun(@addpath, testCase.TestPaths)
        end
    end

    methods (TestClassTeardown)
        function removeFunctionPath(testCase)
            cellfun(@rmpath, testCase.TestPaths)
        end
    end

    methods (Test)
        function testReturnExceptionOnReset(testCase)
        % Test that an exception can be returned and reset
            testMessage = 'Test Exception';
            jupyter.getOrStashExceptions(testMessage, false); % Stash the exception without the intention to reset
            result = jupyter.getOrStashExceptions([], true); % Retrieve and reset
            testCase.assertEqual(result, testMessage, ...
                                 'The function should return the Test Exception when resetFlag is true.');
            resultAfterReset = jupyter.getOrStashExceptions();
            testCase.assertEmpty(resultAfterReset, ...
                                 'The stashed exception should be cleared after being reset.');
        end

        function testReturnStashedExceptionWithoutReset(testCase)
        % Test that the stashed exception is returned without resetting
            testMessage = 'Test Exception';
            jupyter.getOrStashExceptions(testMessage); % Stash the exception
            result = jupyter.getOrStashExceptions(); % Retrieve without resetting
            testCase.assertEqual(result, testMessage);
        end
    end
end
