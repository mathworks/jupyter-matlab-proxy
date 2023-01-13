% IMPORTANT NOTICE:
% This file may contain calls to MathWorks internal APIs which are subject to
% change without any prior notice. Usage of these undocumented APIs outside of
% these files is not supported.

function result = execute(code)
% EXECUTE A helper function for handling execution of MATLAB code and post-processing
% the outputs to conform to Jupyter API. We use the Live Editor API for majority
% of the work.
%
% The entire MATLAB code given by user is treated as code within a single cell
% of a unique Live Script. Hence, each execution request can be considered as
% creating and running a new Live Script file.

% Copyright 2023 The MathWorks, Inc.

% Embed user MATLAB code in a try-catch block for MATLAB versions less than R2022b.
% This is will disable inbuilt ErrorRecovery mechanism. Any exceptions created in
% user code would be handled by +jupyter/getOrStashExceptions.m
if verLessThan('matlab', '9.13')
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
jsonedRegionList = jsonencode(struct(...
    'regionLineNumber',1,...
    'regionString',code,...
    'regionNumber',0,...
    'endOfSection',true,...
    'sectionNumber',1));
request = struct('requestId', 'jupyter_matlab_kernel',...
    'regionArray', jsonedRegionList,...
    'fullText', code,...
    'fullFilePath', fileToShowErrors);

% Disable Hotlinks in the output captured. The hotlinks do not have a purpose
% in Jupyter notebooks.
previousState = feature('hotlinks','off');

% Use the Live editor API for execution of MATLAB code and capturing the outputs
resp = jsondecode(matlab.internal.editor.evaluateSynchronousRequest(request));

% Reset the hotlinks feature.
feature('hotlinks',previousState);

% Post-process the outputs to conform to Jupyter API.
result = processOutputs(resp.outputs);

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
            result{ii} = processVariable(outputData);
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
text = sprintf("%s = %s\n   %s", output.name, output.header, strtrim(output.value));
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
    if verLessThan('matlab','9.11')
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
% base64Data will be "data:image/png;base64,<base64_value>"
function result = processFigure(base64Data)
result.type = 'execute_result';
base64DataSplit = split(base64Data,";");
result.mimetype = {extractAfter(base64DataSplit{1},5)};
result.value = {extractAfter(base64DataSplit{2},7)};

% Helper function to notify browser page load finished
function pageLoadCallback(~,~,idler)
idler.stopIdling();
