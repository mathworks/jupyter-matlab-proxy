% Copyright 2024 The MathWorks, Inc.

classdef TestCompleteFunction < matlab.unittest.TestCase
% TestCompleteFunction contains unit tests for the complete function

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
        function testBasicCompletion(testCase)
        % Test basic completion functionality
            code = 'plo';
            cursorPosition = 2;
            result = jupyter.complete(code, cursorPosition);
            expectedMatches = 'plot';
            testCase.verifyTrue(ismember(expectedMatches, result.matches), "Completion 'plot' was not found in the result");
        end

        function testEmptyCode(testCase)
        % Test behavior with empty code string
            code = '';
            cursorPosition = 0;
            result = jupyter.complete(code, cursorPosition);
            testCase.verifyTrue(isempty(result.matches));
        end

        function testInvalidCursorPosition(testCase)
        % Test behavior with an invalid cursor position
            code = 'plot';
            cursorPosition = -1; % Invalid cursor position
            result = jupyter.complete(code, cursorPosition);
            testCase.verifyTrue(isempty(result.matches));
        end
    end
end
