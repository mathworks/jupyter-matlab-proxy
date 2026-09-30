% IMPORTANT NOTICE:
% This file may contain calls to MathWorks internal APIs which are subject to
% change without any prior notice. Usage of these undocumented APIs outside of
% these files is not supported.

function result = execute(code, kernelId)
% EXECUTE A helper function for handling execution of MATLAB code and capturing
% the raw outputs. We use the Live Editor API for majority of the work.
%
% The entire MATLAB code given by user is treated as code within a single cell
% of a unique Live Script. Hence, each execution request can be considered as
% creating and running a new Live Script file.

% Copyright 2023-2026 The MathWorks, Inc.

% Embed user MATLAB code in a try-catch block for MATLAB versions less than R2022b.
% This is will disable inbuilt ErrorRecovery mechanism. Any exceptions created in
% user code would be handled by +jupyter/getOrStashExceptions.m
if isMATLABReleaseOlderThan("R2022b")
    code = sprintf(['try\n'...
        '%s\n'...
        'catch JupyterKernelME\n'...
        'jupyter.getOrStashExceptions(JupyterKernelME)\n'...
        'clear JupyterKernelME\n'...
        'end'], code);
end

% Value that needs to be shown in the error message when a particular error
% displays the file name. The kernel does not have access to the file name
% of the IPYNB file. Hence, we use a generic name 'Notebook' for the time being.
fileToShowErrors = 'Notebook';

% Prepare the input for the Live Editor API.
% 'requestId'   - char array - UUID
% 'editorId'    - char array - unique identifier usually corresponding to a file.
request = struct('requestId', 'jupyter_matlab_kernel',...
    'editorId', kernelId,...
    'fullText', code,...
    'fullFilePath', fileToShowErrors);

% Update additional fields in the request based on MATLAB and LiveEditor API version.
request = updateRequest(request, code);

% Disable Hotlinks in the output captured. The hotlinks do not have a purpose
% in Jupyter notebooks.
hotlinksPreviousState = feature('hotlinks','off');
hotlinksCleanupObj = onCleanup(@() feature('hotlinks', hotlinksPreviousState));

% Figures hang in MATLAB versions >= R2025a for certain workflows. The following
% workaround fixes the issue in MATLAB versions >= R2025b.
if ~isMATLABReleaseOlderThan("R2025b")
    forceIndependentlyHostedFiguresProp = addprop(groot, "ForceIndependentlyHostedFigures");
    propCleanupObj = onCleanup(@() delete(forceIndependentlyHostedFiguresProp));
end

% Use the Live editor API for execution of MATLAB code and capturing the outputs
resp = jsondecode(matlab.internal.editor.evaluateSynchronousRequest(request));

% Append any stashed exceptions to the outputs.
ME = jupyter.getOrStashExceptions([], true);
if ~isempty(ME)
    resp.outputs = [resp.outputs, struct('type', 'stderr', ...
        'outputData', struct('text', ...
        getReport(ME, 'extended', 'hyperlinks', 'off')), ...
        'lineNumbers', [])];
end

result = resp.outputs;

% Helper function to update fields in the request based on MATLAB and LiveEditor
% API version.
function request = updateRequest(request, code)
% Support for MATLAB version <= R2023a.
if isMATLABReleaseOlderThan("R2023b")
    request = updateRequestFromBefore23b(request, code);
else
    % Support for MATLAB version >= R2023b.
    
    % To maintain backwards compatibility, each case in the switch
    % encodes conversion from the version number in the case
    % to the current version.
    switch matlab.internal.editor.getApiVersion('synchronous')
        case 1
            request = updateRequestFromVersion1(request, code);
        case 2
            request = updateRequestFromVersion2(request, code);
        otherwise
            error("Invalid API version. Create an issue at https://github.com/mathworks/jupyter-matlab-proxy for further support.");
    end
end

% Helper function to update fields in the request for MATLAB versions less than
% R2023b
function request = updateRequestFromBefore23b(request, code)
jsonedRegionList = jsonencode(struct(...
    'regionLineNumber',1,...
    'regionString',code,...
    'regionNumber',0,...
    'endOfSection',true,...
    'sectionNumber',1));
request.regionArray = jsonedRegionList;

% Helper function to update fields in the request when LiveEditor API version is 1.
function request = updateRequestFromVersion1(request, code)
request.sectionBoundaries = [];
request.startLine = 1;
request.endLine = builtin('count', code, newline) + 1;

% Allow figures to be used across Notebook cells. Cleanup needs to be
% done explicitly when the kernel shutsdown.
request.shouldResetState = false;
request.shouldDoFullCleanup = false;

% Helper function to update fields in the request when LiveEditor API version is 2.
function request = updateRequestFromVersion2(request, code)
request = updateRequestFromVersion1(request, code);

% Request MIME based outputs.
request.preferBasicOutputs = true;
