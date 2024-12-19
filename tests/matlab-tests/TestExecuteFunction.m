% Copyright 2024 The MathWorks, Inc.
classdef TestExecuteFunction < matlab.unittest.TestCase
    % TestExecuteFunction contains unit tests for the execute function
    properties
        TestPaths
    end

    methods (TestClassSetup)
        function addFunctionPath(testCase)
            testCase.TestPaths = cellfun(@(relative_path)(fullfile(pwd, relative_path)), {"../../src/jupyter_matlab_kernel/matlab"}, 'UniformOutput', false);
            cellfun(@addpath, testCase.TestPaths)
        end
        function suppressWarnings(testCase)
            warning('off', 'all');
            testCase.addTeardown(@() warning('on', 'all'));
        end        
    end

    methods (TestClassTeardown)
        function removeFunctionPath(testCase)
            cellfun(@rmpath, testCase.TestPaths)
        end
    end
    methods (Test)
        function testMatrixOutput(testCase)
            % Test execution of a code that generates a matrix output
            code = 'repmat([1 2 3 4],5,1)';
            kernelId = 'test_kernel_id';
            result = jupyter.execute(code, kernelId);
            testCase.verifyEqual(result{1}.type, 'execute_result', 'Expected execute_result type');
            testCase.verifyTrue(any(strcmp(result{1}.mimetype{1}, 'text/html')), 'Expected HTML output');
            testCase.verifyTrue(any(strcmp(result{1}.mimetype{2}, 'text/plain')), 'Expected HTML output');
            testCase.verifySubstring(result{1}.value{1}, 'ans = 5');
        end

        function testVariableOutput(testCase)
            % Test execution of a code that generates a variable output
            code = 'var x';
            kernelId = 'test_kernel_id';
            result = jupyter.execute(code, kernelId);
            testCase.verifyEqual(result{1}.type, 'execute_result', 'Expected execute_result type');
            testCase.verifyTrue(any(strcmp(result{1}.mimetype{1}, 'text/html')), 'Expected HTML output');
            testCase.verifyTrue(any(strcmp(result{1}.mimetype{2}, 'text/plain')), 'Expected HTML output');
            testCase.verifySubstring(result{1}.value{1}, 'ans = 0');
        end
        
        %Skipping the following test as it fails in public github run
        % function testSymbolicOutput(testCase)
        %     %Test execution of a code that generates a symbolic output
        %     code = 'x = sym(1/3); disp(x);';
        %     kernelId = 'test_kernel_id';
        %     result = jupyter.execute(code, kernelId);
        %     testCase.verifyEqual(result{1}.type, 'execute_result', 'Expected execute_result type');
        %     testCase.verifyTrue(any(strcmp(result{1}.mimetype{1}, ["text/latex", "text/html"])), 'Expected LaTeX or HTML output');
        % end

        function testErrorOutput(testCase)
            % Test execution of a code that generates an error
            code = 'error(''Test error'');';
            kernelId = 'test_kernel_id';
            result = jupyter.execute(code, kernelId);
            testCase.verifyEqual(result{1}.type, 'stream', 'Expected stream type');
            testCase.verifyEqual(result{1}.content.name, 'stderr', 'Expected stderr stream');
            testCase.verifyTrue(contains(result{1}.content.text, 'Test error'), 'Expected error message');
        end

        function testFigureOutput(testCase)
            % Test execution of a code that generates a figure output
            code = 'figure; plot(1:10); title(''Test Figure'');';
            kernelId = 'test_kernel_id';
            result = jupyter.execute(code, kernelId);
            testCase.verifyEqual(result{1}.type, 'execute_result', 'Expected execute_result type');
            testCase.verifyTrue(any(strcmp(result{1}.mimetype, 'image/png')), 'Expected PNG image output');
            testCase.verifyTrue(~isempty(result{1}.value{1}));
        end
    end
end