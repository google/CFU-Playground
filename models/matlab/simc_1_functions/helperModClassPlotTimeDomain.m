function helperModClassPlotTimeDomain(dataDirectory,modulationTypes,fs)
%helperModClassPlotTimeDomain Time domain plots of frames
%   helperModClassPlotTimeDomain(DIR,MODTYPES,FS) plots a spectrogram for
%   each modulation type specified in MODTYPES using datafiles in the DIR
%   folder. FS is the sample rate.
%   
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2019 The MathWorks, Inc.

numRows = ceil(length(modulationTypes) / 4);
for modType=1:length(modulationTypes)
  subplot(numRows, 4, modType);
  files = dir(fullfile(dataDirectory,"*" + string(modulationTypes(modType)) + "*"));
  idx = randi([1 length(files)]);
  load(fullfile(files(idx).folder, files(idx).name), 'frame');

  spf = size(frame,1);
  t = 1000*(0:spf-1)/fs;

  plot(t,real(frame), '-'); grid on; axis equal; axis square
  hold on
  plot(t,imag(frame), '-'); grid on; axis equal; axis square
  hold off
  title(string(modulationTypes(modType)));
  xlabel('Time (ms)'); ylabel('Amplitude')
end
end