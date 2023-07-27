% Copyright 2023 The MathWorks, Inc.

classdef TestSimpleAddition < matlab.unittest.TestCase

    methods (Test)
        function testSimpleAddition(testCase)
            % Test case for a simple addition

            a = 2;
            b = 3;

            expected = 5;

            actual = a + b;

            testCase.verifyEqual(actual, expected);
        end
    end
end