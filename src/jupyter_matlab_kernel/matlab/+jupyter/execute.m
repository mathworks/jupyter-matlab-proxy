% IMPORTANT NOTICE:
% This file may contain calls to MathWorks internal APIs which are subject to
% change without any prior notice. Usage of these undocumented APIs outside of
% these files is not supported.

function result = execute(code, kernelId)
% EXECUTE A helper function for handling execution of MATLAB code and post-processing
% the outputs to conform to Jupyter API. We use the Live Editor API for majority
% of the work.
%
% The entire MATLAB code given by user is treated as code within a single cell
% of a unique Live Script. Hence, each execution request can be considered as
% creating and running a new Live Script file.

% Copyright 2023-2024 The MathWorks, Inc.

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

% Use the Live editor API for execution of MATLAB code and capturing the outputs
resp = jsondecode(matlab.internal.editor.evaluateSynchronousRequest(request));

% Post-process the outputs to conform to Jupyter API.
result = processOutputs(resp.outputs);

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

% Helper function to process different types of outputs given by LiveEditor API.
function result = processOutputs(outputs)
result =cell(1,length(outputs));
figureTrackingMap = containers.Map;

% Post process each captured output based on its type.
for ii = 1:length(outputs)
    out = outputs(ii);
    outputData = out.outputData;
    switch out.type
        case 'matrix'
            result{ii} = processMatrix(outputData);
        case 'variable'
            result{ii} = processVariable(outputData);
        case 'variableString'
            result{ii} = processVariableString(outputData);
        case 'symbolic'
            result{ii} = processSymbolic(outputData);
        case 'error'
            result{ii} = processStream('stderr', outputData.text);
        case 'warning'
            result{ii} = processStream('stderr', outputData.text);
        case 'text'
            result{ii} = processStream('stdout', outputData.text);
        case 'stderr'
            result{ii} = processStream('stderr', outputData.text);
        case 'figure'
            % 'figure' outputType may not necessarily contain the actual image.
            % Hence, if the 'figure' is a placeholder, we store its position in
            % a map to preserve the ordering. In a later 'figure' output, if the
            % actual image data is present, we store the image in the corresponding
            % placeholder position if it exists, else the current position.
            if isfield(outputData, 'figurePlaceHolderId')
                id = outputData.figurePlaceHolderId;
                if ~figureTrackingMap.isKey(id)
                    figureTrackingMap(id) = ii;
                end
            elseif isfield(outputData, 'figureImage')
                id = outputData.figureId;
                if figureTrackingMap.isKey(id)
                    idx = figureTrackingMap(id);
                else
                    idx = ii;
                end
                result{idx} = processFigure(outputData.figureImage);
            end
        case 'text/html'
            result{ii} = processHtml(outputData);
    end
end

ME = jupyter.getOrStashExceptions([], true);
if ~isempty(ME)
    result{end+1} = processStream('stderr', ME.message);
end

% Helper functions to post process output of type 'matrix', 'variable' and
% 'variableString'. These outputs are of HTML type due to various HTML tags
% used in MATLAB outputs such as the <strong> tag in tables.
function result = processText(text)
result.type = 'execute_result';
result.mimetype = {"text/html", "text/plain"};
result.value = [sprintf("<html><body><pre>%s</pre></body></html>",text), text];

function result = processMatrix(output)
text = sprintf("%s = %s %s\n%s", output.name, output.header, output.type, output.value);
if output.rows > 10 || output.columns > 30
    text = strcat(text, "...");
end
result = processText(text);

function result = processVariable(output)
if isempty(output.header)
    indentation = '';
else
    indentation = sprintf('\n    ');
end
text = sprintf("%s = %s%s%s", output.name, output.header, indentation, output.value);
result = processText(text);

function result = processVariableString(output)
indentation = '';
useSingleLineDisplay = ~(builtin('contains', output.value, newline));
if useSingleLineDisplay
    if ~isempty(output.header)
        indentation = sprintf(newline);
    end
else
    indentation = sprintf(newline);
end
text = sprintf("%s = %s%s%s", output.name, output.header, indentation, output.value);
result = processText(text);

% Helper function for post-processing symbolic outputs. The captured output
% contains MathML representation of symbolic expressions. Since Jupyter and
% GitHub have native support for LaTeX, we use EquationRenderer JS API to
% convert the MathML to LaTeX values.
function result = processSymbolic(output)
% Use persistent variables to avoid loading multiple webwindows.
persistent webwindow;
persistent idler;

if isempty(webwindow)
    url = 'toolbox/matlab/codetools/liveeditor/index.html';
    
    % MATLAB versions R2020b and R2021a requires specifying the base url.
    % Not doing so results in the URL not being loaded with the error
    %"Not found. Request outside of context root".
    if isMATLABReleaseOlderThan("R2021b")
        url = strcat(getenv("MWI_BASE_URL"), '/', url);
    end
    webwindow = matlab.internal.cef.webwindow(connector.getUrl(url));
    idler = jupyter.Idler;
    webwindow.PageLoadFinishedCallback = @(a,b) pageLoadCallback(a,b,idler);
end

% This will block the thread until stop loading is called. The values are logical
pageLoaded = idler.startIdling(10);

% If page is not loaded succesfully. We fallback to embedding MathML inside HTML.
% This will render the symbolic output in JupyterLab and Classic Notebook but not
% in GitHub.
if ~pageLoaded
    result = processText(output.value);
    return
end

%  Use the EquationRenderer JS API to convert MathML to LaTeX.
webwindow.executeJS('eq = require("equationrenderercore/EquationRenderer")');
latexcode = jsondecode(webwindow.executeJS(sprintf('eq.convertMathMLToLaTeX(%s)', jsonencode(output.value))));
if isempty(output.name)
    % If there is no variable name captured, then we only display the symbolic equation.
    % This happens in cases such as "disp(exp(b))".
    latexcode = strcat('$',latexcode,'$');
else
    latexcode = strcat('$',output.name,' = ',latexcode,'$');
end

result.type = 'execute_result';
result.mimetype = {"text/latex"};
result.value = {latexcode};

% Helper function for processing outputs of stream type such as 'stdout' and 'stderr'
function result = processStream(stream, text)
result.type = 'stream';
result.content.name = stream;
result.content.text = text;

% Helper function for processing figure outputs.
% base64Data will be 'data:image/png;base64,<base64_value>'
function result = processFigure(base64Data)
pattern = "data:(?<mimetype>.*);base64,(?<value>.*)";
result = builtin('regexp', base64Data, pattern, 'names');
assert(builtin('startsWith', result.mimetype, 'image'), 'Error in processFigure. ''mimetype'' is not an image');
assert(~isempty(result.value), 'Error in processFigure. ''value'' is empty');
result.mimetype = {result.mimetype};
result.value = {result.value};
result.type = 'execute_result';

% Helper function for processing text/html mime-type outputs.
function result = processHtml(text)
result.type = 'execute_result';
result.mimetype = {"text/html", "text/plain"};
result.value = [sprintf("%s",text), text];

% Helper function to notify browser page load finished
function pageLoadCallback(webwindow,~,idler)
idler.stopIdling();
% Disable alert box which is preventing running JS after certain period of time.
webwindow.executeJS('window.alert = function(){}');
