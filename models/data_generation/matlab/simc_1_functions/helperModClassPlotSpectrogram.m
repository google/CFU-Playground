function helperModClassPlotSpectrogram(dataDirectory,modulationTypes,fs,sps)
%helperModClassPlotSpectrogram Spectrogram of frames
%   helperModClassPlotSpectrogram(DIR,MODTYPES,FS,SPS) plots a spectrogram
%   for each modulation type specified in MODTYPES using datafiles in the
%   DIR folder. FS is the sample rate. SPS is the samples per symbol.
%   
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2019 The MathWorks, Inc.

figure
numRows = ceil(length(modulationTypes) / 4);
for modType=1:length(modulationTypes)
  subplot(numRows, 4, modType);
  files = dir(fullfile(dataDirectory,"*" + string(modulationTypes(modType)) + "*"));
  idx = 10;
  load(fullfile(files(idx).folder, files(idx).name), 'frame');

  spectrogram(frame,kaiser(sps),0,1024,fs,'centered');
  title(string(modulationTypes(modType)));
end
h = gcf; delete(findall(h.Children, 'Type', 'ColorBar'))
end
