function framec = helperModClassReadFrame(in)
%helperModClassReadFrame Read frame data from the files
%   FRAMEC = helperModClassReadFrame(IN) extracts the frame data from
%   input, IN, which is a cell array where the first element is the complex
%   frame and the second element is the label string. The output, FRAMEC,
%   is the frame data in a cell array. 
%   
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2019 The MathWorks, Inc.

framec = in(1);
end

