function [returnedException] = getOrStashExceptions(exceptionMessage, resetFlag)
% getOrStashExceptions will save the given exception in a persistent variable
% to provide access later on.

% Passing in an exceptionMessage will always stash it
% When resetFlag is set, old exceptionMessage if any is returned, and is
% cleared.

% Copyright 2023 The MathWorks, Inc.

persistent stashedException

% Initialize the persistent variable if it is not already done.
if isempty(stashedException)
    stashedException = [];
end

% When resetFlag is set, return the saved exception as output and reset the
% saved exception.
if nargin == 2 && resetFlag == true
    returnedException = stashedException;
    stashedException = [];
    return
end

% If there are no input arguments, only return the saved exception
if nargin == 0
    returnedException = stashedException;
    return
end

% Update the saved exception with the given exception.
stashedException = exceptionMessage;
