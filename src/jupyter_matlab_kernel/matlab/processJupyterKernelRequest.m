function result = processJupyterKernelRequest(request_type, execution_request_type, varargin)
% PROCESSJUPYTERKERNELREQUEST An entrypoint function for various Jupyter Kernel
% features such as code execution, code completion etc.
%   Inputs:
%       request_type - string     - identifier to differentiate multiple features.
%                                   Supported values are "execute" and "complete"
%       execution_request_type - string - identifier to differentiate how this
%                                   function is run in MATLAB. Supported values
%                                   are "feval" and "eval"
%       varargin     - cell array - additional inputs which vary in number based
%                                   on value of input request_type
%                                   - "execute"
%                                      - string - MATLAB code to be executed
%                                      - string - ID of the kernel
%                                   - "complete"
%                                      - string - MATLAB code
%                                      - number - cursor position
%                                   - "shutdown"
%                                      - string - ID of the kernel
%   Outputs:
%       Varies by request_type:
%       - "execute": cell array of structs, each with:
%           - type       - string - output type. Supported values: "matrix",
%                                   "variable", "variableString", "symbolic",
%                                   "text", "warning", "error", "stderr",
%                                   "figure", "text/html", "markdown"
%           - outputData - value whose shape varies by type (see OutputProcessor)
%       - "complete": struct with:
%           - matches     - cell array - completion match strings
%           - completions - cell array of structs (text, type, start, end)
%           - start       - number - start of replacement range
%           - end         - number - end of replacement range
%       - "shutdown": empty cell array {}
%       - "convertMathMLToLaTeX": string - LaTeX representation
%

% Copyright 2023-2026 The MathWorks, Inc.

% Lock the function on the first use to prevent it from being cleared from the memory
mlock;

% If the first argument is received through an eval request, it will be JSON
% encoded to prevent the eval string from being broken by special characters.
% Decode it back to get the original value.
if execution_request_type == "eval"
    varargin{1} = jsondecode(varargin{1});
end

% Delegate feature work based on request type
try
    switch(request_type)
        case 'execute'
            code = varargin{1};
            kernelId = varargin{2};
            output = jupyter.execute(code, kernelId);
        case 'complete'
            code = varargin{1};
            cursorPosition = varargin{2};
            output = jupyter.complete(code, cursorPosition);
        case 'shutdown'
            kernelId = varargin{1};
            output = jupyter.shutdown(kernelId);
        case 'convertMathMLToLaTeX'
            mathml = varargin{1};
            output = jupyter.convertMathMLToLaTeX(mathml);
    end
catch ME
    % The code withing try block should be exception safe. In case anything we
    % have missed an edge case, catch the exception and send it to the user.
    errMsg = sprintf('MATLAB Kernel Error:\n%s', ...
        getReport(ME, 'extended', 'hyperlinks', 'off'));
    output = {struct('type', 'stderr', ...
        'outputData', struct('text', errMsg))};
end

if execution_request_type == "feval"
    result = output;
elseif execution_request_type == "eval"
    % Create a temporary file to store the current results.
    tname = [tempname(getenv("MATLAB_LOG_DIR")) '.txt'];

    % Write the JSON to the temporary file.
    fid = fopen(tname, 'w');
    fwrite(fid, jsonencode(output));
    fclose(fid);

    % Display the path of temporary file so that it is captured as response
    % to the eval execution request type.
    disp(tname)
end

end
