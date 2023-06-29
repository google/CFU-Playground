function out = helperModClassIQAsPages(in)
%helperModClassIQAsPages Transform complex input to I/Q as pages
%   OUT = helperModClassIQAsPages(IN) transforms input, IN, which is a cell
%   array where the first element is the complex frame and the second
%   element is the label string. The output, OUT, has a frame where I/Q are
%   placed in the third dimension, separately, such that the size of the
%   output frame is [1xSPFx2], where SPF is samples per frame. 
%   
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2019 The MathWorks, Inc.

frameComplex = in{1};
frameLabel = in{2};

I = permute(real(frameComplex), [2 1]);
Q = permute(imag(frameComplex), [2 1]);
frameReal = cat(3, I, Q);


out = {frameReal, frameLabel};
end

