classdef Idler < handle
    % Object that idles until told to stop idling or until a specified
    % amount of time has passed.
    %
    % Idler methods:
    %   Idler       - Creates an instance of an idler
    %   startIdling - Starts idling for up to a specified time
    %   stopIdling  - Stops idling
    
    %   Copyright 2023 The MathWorks, Inc.
    methods
        
        function obj = Idler()
            % Idler Creates idler instance
            obj.TimedOut = false;
            obj.Status = false;
        end
        
        function status = startIdling(obj, maxIdleTime)
            % startIdling Cause the idler to start idling
            % status = startIdling(idler, timeout) causes the idler to
            % idle until its stopIdling method is called or until the
            % specified maximum idle time has elapsed. This method 
            % returns true if it stops idling before the maximum idle
            % time has elapsed; otherwise, false.
            timerFcn = @(~,~)(obj.timedOut());
            timerObj = timer('StartDelay', maxIdleTime, ...
                'TimerFcn', timerFcn ,'ExecutionMode', 'singleShot');
            cleanObj = onCleanup(@()delete(timerObj));
            start(timerObj);
            if ~obj.Status
                waitfor(obj, 'Status', true)
            end
            stop(timerObj);
            
            status = obj.Status && (~obj.TimedOut);
        end
        
        function stopIdling(obj)
            % stopIdling Causes the idler to stop idling.
            obj.Status = true;
        end
        
    end
    
    properties (Hidden)
        Status
        TimedOut
    end
    
    methods (Hidden)
        
        function timedOut(obj)
            obj.TimedOut = true;
            obj.Status = true;
        end
        
        
    end
end