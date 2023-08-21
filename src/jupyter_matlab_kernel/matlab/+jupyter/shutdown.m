% IMPORTANT NOTICE:
% This file may contain calls to MathWorks internal APIs which are subject to
% change without any prior notice. Usage of these undocumented APIs outside of
% these files is not supported.

function output = shutdown(kernelId)
% SHUTDOWN A helper function to perform cleanup activities when a kernel shuts down.

% Copyright 2023 The MathWorks, Inc.

import matlab.internal.editor.SynchronousEvaluationOutputsService

% Perform LiveEditor state cleanup of a given notebook in MATLAB versions >= R2023b
if ~isMATLABReleaseOlderThan("R2023b")
    SynchronousEvaluationOutputsService.cleanup(kernelId);
end

output = {};
end