function [trainDS,validDS,testDS] = helperModClassSplitData(frameDS,splitPercentages)
%helperModClassSplitData Split data into training, validation and test
%   [TRAIN,VALID,TEST]=splitData(FRAMES,PER) splits the frames in the
%   FRAMES datastore into training, validation, and test groups based on
%   the percentages, PER. PER is a three-element vector,
%   [PERTRAIN,PERVALID,PERTEST], which specifies training, validation, and
%   test percentages. TRAIN, VALID, and TEST are the datastores for
%   training, validation, and test frames.
%
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2019 The MathWorks, Inc.

percentTrainingSamples = splitPercentages(1);
percentValidationSamples = splitPercentages(2);
percentTestSamples = splitPercentages(3);

labels = transform(frameDS, @helperModClassReadLabel);
rxLabels = readall(labels,'UseParallel',parallelComputingLicenseExists());
modulationTypes = unique(rxLabels);

numFrames = length(rxLabels);
numTrainFrames = round(numFrames*percentTrainingSamples/100);
numValidFrames = round(numFrames*percentValidationSamples/100);
numTestFrames = round(numFrames*percentTestSamples/100);
extraFrames = sum([numTrainFrames,numValidFrames,numTestFrames]) - numFrames;
if (extraFrames > 0)
  numTestFrames = numTestFrames - extraFrames;
end

trainIdx = zeros(numTrainFrames,1);
validIdx = zeros(numValidFrames,1);
testIdx = zeros(numTestFrames,1);
trainFrameCnt = 0;
validFrameCnt = 0;
testFrameCnt = 0;

for modType = 1:length(modulationTypes)
  rawIdx = find(rxLabels == modulationTypes(modType));
  numFrames = length(rawIdx);

  % Determine the number of frames for training, test, and validation
  numTrainFrames = round(numFrames*percentTrainingSamples/100);
  numValidFrames = round(numFrames*percentValidationSamples/100);
  numTestFrames = round(numFrames*percentTestSamples/100);
  extraFrames = sum([numTrainFrames,numValidFrames,numTestFrames]) - numFrames;
  if (extraFrames > 0)
    numTestFrames = numTestFrames - extraFrames;
  end

  trainIdx((1:numTrainFrames)+trainFrameCnt,1) = rawIdx(1:numTrainFrames,1);
  trainFrameCnt = trainFrameCnt + numTrainFrames;

  validIdx((1:numValidFrames)+validFrameCnt,1) = rawIdx(1:numValidFrames,1);
  validFrameCnt = validFrameCnt + numValidFrames;

  testIdx((1:numTestFrames)+testFrameCnt,1) = rawIdx(1:numTestFrames,1);
  testFrameCnt = testFrameCnt + numTestFrames;
end

trainDS = subset(frameDS, trainIdx);
validDS = subset(frameDS, validIdx);
testDS = subset(frameDS, testIdx);
