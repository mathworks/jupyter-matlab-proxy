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
%       - cell array on struct
%           - type      - string - jupyter output type. Supported values are
%                                  "execute_result" and "stream"
%           - mimetype  - cell array - mimetypes of the outputs. Usually these are
%                                      different representations for the same output.
%           - value     - cell array - Output value corresponding to the representation
%                                      of mimetype at its index.
%           - content   - struct - Used only for 'stream' type
%               - name  - string - name of the stream. Supported values are 'stdout'
%                                  and 'stderr'.
%               - value - string - content of the stream
%

% Copyright 2023 The MathWorks, Inc.

% Lock the function on the first use to prevent it from being cleared from the memory
mlock;

code = varargin{1};

% If the code is received through an eval request, it will be JSON encoded to
% prevent the eval string to be broken down by MATLAB due to formatting. We need
% to decode the received code to get the original user code. For example
% "processJupyterKernelRequest('execute', 'eval', 'a = "Hello\\n''world''"')".
if execution_request_type == "eval"
    code = jsondecode(code);
end

% Delegate feature work based on request type
try
    switch(request_type)
        case 'execute'
            kernelId = varargin{2};
            output = jupyter.execute(code, kernelId);
        case 'complete'
            cursorPosition = varargin{2};
            output = jupyter.complete(code, cursorPosition);
        case 'shutdown'
            kernelId = varargin{1};
            output = jupyter.shutdown(kernelId);
    end
catch ME
    % The code withing try block should be exception safe. In case anything we
    % have missed an edge case, catch the exception and send it to the user.
    errorMessage.type = 'stream';
    errorMessage.content.name = 'stderr';
    errorMessage.content.text = sprintf('MATLAB Kernel Error:\n%s', getReport(ME));
    output = {errorMessage};
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
