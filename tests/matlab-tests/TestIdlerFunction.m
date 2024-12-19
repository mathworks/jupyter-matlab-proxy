% Copyright 2024 The MathWorks, Inc.
classdef TestIdlerFunction < matlab.unittest.TestCase
    % Unit tests for the Idler class
    properties
        TestPaths
    end

    methods (TestClassSetup)
        function addFunctionPath(testCase)
            testCase.TestPaths = cellfun(@(relative_path)(fullfile(pwd, relative_path)), {"../../src/jupyter_matlab_kernel/matlab"}, 'UniformOutput', false);
            cellfun(@addpath, testCase.TestPaths)
        end
    end

    methods (TestClassTeardown)
        function removeFunctionPath(testCase)
            cellfun(@rmpath, testCase.TestPaths)
        end
    end

    properties
        Idler
    end
    
    methods(TestMethodSetup)
        function createIdler(testCase)
            testCase.Idler = jupyter.Idler;
        end
    end
    
    methods(Test)
        function testIdlerInitialization(testCase)
            %Initially the idler should not be timed out and its status should be false
            testCase.verifyFalse(testCase.Idler.TimedOut);
            testCase.verifyFalse(testCase.Idler.Status);
        end
        
        function testStartIdlingTimeout(testCase)
            %Verify that the startIdling function times out after the 1second
            maxIdleTime = 1; % 1second
            tic;
            status = testCase.Idler.startIdling(maxIdleTime);
            elapsedTime = toc;
            testCase.verifyFalse(status);
            testCase.verifyGreaterThanOrEqual(elapsedTime, maxIdleTime);
            testCase.verifyTrue(testCase.Idler.TimedOut);
            testCase.verifyTrue(testCase.Idler.Status);
        end
        
        function testStopIdling(testCase)
            %Verify that the stopIdling function stops the idling process before timeout
            maxIdleTime = 5;
            % Timer function triggering stopIdling after a delay of 0.5s to
            % stop the startIdling function
            timerObj = timer('StartDelay', 0.5, 'TimerFcn', @(~,~)testCase.Idler.stopIdling());
            start(timerObj);
            status = testCase.Idler.startIdling(maxIdleTime);
            stop(timerObj);
            delete(timerObj);
            testCase.verifyTrue(status);
            testCase.verifyTrue(testCase.Idler.Status);
            testCase.verifyFalse(testCase.Idler.TimedOut);
        end
    end
end