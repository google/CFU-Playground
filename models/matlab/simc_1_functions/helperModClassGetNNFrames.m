function framesReal = helperModClassGetNNFrames(rx)
%helperModClassGetNNFrames Generate formatted frames for neural networks
%   F = helperModClassGetNNFrames(X) formats the input X, into
%   frames that can be used with the neural network designed in this
%   example, and returns the frames in the output F.
%   
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2019 The MathWorks, Inc.

framesComplex = helperModClassFrameGenerator(rx,1024,1024,32,8);

I = permute(real(framesComplex), [3 1 4 2]);
Q = permute(imag(framesComplex), [3 1 4 2]);
framesReal = cat(3, I, Q);
end