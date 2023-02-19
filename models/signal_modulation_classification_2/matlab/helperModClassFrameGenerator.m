function y = helperModClassFrameGenerator(x, windowLength, stepSize, offset, sps)
%helperModClassFrameGenerator Generate frames for machine learning
%   Y = helperModClassFrameGenerator(X,WLEN,STEP,OFFSET,SPS) segments the
%   input, X, to generate frames to be used in machine learning algorithms.
%   X must be a complex-valued column vector. The output, Y, is a size
%   WLENxN complex-valued array, where N is the number of output frames.
%   Each individual frame has WLEN samples. The window is progressed STEP
%   samples for the new frame. STEP can be smaller or greater than WLEN.
%   The function starts segmenting the input, X, after it calculates an
%   initial offset based on the OFFSET value. OFFSET is the deterministic
%   offset value specified as a real-valued scalar. SPS is the number of
%   samples per symbol. Total offset is OFFSET+randi([0 SPS]) samples. The
%   deterministic part of the offset removes transients, while the random
%   part enables the network to adapt to unknown delay values. Each frame
%   is normalized to have unit energy.
%
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2018 The MathWorks, Inc.


numSamples = length(x);
numFrames = ...
  floor(((numSamples-offset)-(windowLength-stepSize))/stepSize);

y = zeros([windowLength,numFrames],class(x));

startIdx = offset + randi([0 sps]);
frameCnt = 1;
while startIdx + windowLength < numSamples
  xWindowed = x(startIdx+(0:windowLength-1),1);
  framePower = mean(abs(xWindowed).^2);
  xWindowed = xWindowed / sqrt(framePower);
  y(:,frameCnt) = xWindowed;
  frameCnt = frameCnt + 1;
  startIdx = startIdx + stepSize;
end
