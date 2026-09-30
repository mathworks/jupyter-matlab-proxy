% Copyright 2024-2026 The MathWorks, Inc.
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
            testCase.verifyEqual(result(1).type, 'matrix', 'Expected raw matrix type');
            testCase.verifySubstring(result(1).outputData.value, '4');
            testCase.verifyEqual(result(1).outputData.rows, 5);
        end

        function testVariableOutput(testCase)
            % Test execution of a code that generates a variable output
            code = 'var x';
            kernelId = 'test_kernel_id';
            if isMATLABReleaseOlderThan("R2024b")
                expected_output_type = 'variable';
            else
                expected_output_type = 'variableString';
            end
            result = jupyter.execute(code, kernelId);
            testCase.verifyEqual(result(1).type, expected_output_type, 'Expected variableString type');
            testCase.verifySubstring(result(1).outputData.value, '0');
        end
        
        function testSymbolicOutput(testCase)
            % Test execution of a code that generates a symbolic output
            code = 'x = sym(1/3); disp(x);';
            kernelId = 'test_kernel_id';
            result = jupyter.execute(code, kernelId);
            testCase.verifyEqual(result(1).type, 'symbolic', ...
                'Expected symbolic type');
            testCase.verifyTrue( ...
                isfield(result(1).outputData, 'value'), ...
                'Expected symbolic value field');
        end

        function testErrorOutput(testCase)
            % Test execution of a code that generates an error
            code = 'error(''Test error'');';
            kernelId = 'test_kernel_id';
            if isMATLABReleaseOlderThan("R2022b")
                expected_output_type = 'stderr';
            else
                expected_output_type = 'error';
            end
            result = jupyter.execute(code, kernelId);
            testCase.verifyEqual(result(1).type, expected_output_type, 'Expected error type');
            testCase.verifyTrue(contains(result(1).outputData.text, 'Test error'), 'Expected error message');
        end

        function testFigureOutput(testCase)
            % Test execution of a code that generates a figure output
            code = 'figure; plot(1:10); title(''Test Figure'');';
            kernelId = 'test_kernel_id';
            result = jupyter.execute(code, kernelId);
            
            hasFigure = false;
            for i = 1:length(result)
                if strcmp(result(i).type, 'figure') && isfield(result(i).outputData, 'figureImage')
                    hasFigure = true;
                end
            end
            testCase.verifyTrue(hasFigure, 'Expected raw figure image output');
        end
    end
end
