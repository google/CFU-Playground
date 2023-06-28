function helperModClassPlotScores(score,labels)
%helperModClassPlotScores Plot classification scores of frames
%   helperModClassPlotScores(SCR,LABELS) plots the classification scores
%   SCR as a stacked bar for each frame. SCR is a matrix in which each row
%   is the score for a frame.
%   
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2019 The MathWorks, Inc.

co = [0.08 0.9 0.49;
  0.52 0.95 0.70;
  0.36 0.53 0.96;
  0.09 0.54 0.67;
  0.48 0.99 0.26;
  0.95 0.31 0.17;
  0.52 0.85 0.95;
  0.08 0.72 0.88;
  0.12 0.45 0.69;
  0.22 0.11 0.49;
  0.65 0.54 0.71];
figure; ax = axes('ColorOrder',co,'NextPlot','replacechildren');
bar(ax,[score; nan(2,11)],'stacked'); legend(categories(labels),'Location','best');
xlabel('Frame Number'); ylabel('Score'); title('Classification Scores')
end