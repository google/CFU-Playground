function testAccuracy = helperModClassSDRTest(radios)
%helperModClassSDRTest Test CNN performance with over-the-air signals
%   A = helperModClassSDRTest sends test frames from an ADALM-PLUTO radio,
%   receives using an ADALM-PLUTO or USRP radio, performs classification
%   with the trained network and returns the overall classification
%   accuracy. Transmitting radio uses transmit-repeat capability to send
%   the same waveform repeatedly without loading the main loop.
%   
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2018-2019 The MathWorks, Inc.

modulationTypes = categorical(["BPSK", "QPSK", "8PSK", ...
  "16QAM", "64QAM", "PAM4", "GFSK", "CPFSK", "B-FM"]);
load trainedModulationClassificationNetwork trainedNet
numFramesPerModType = 100;

sps = 8;                % Samples per symbol
spf = 1024;             % Samples per frame
fs = 200e3;             % Sample rate

txRadio = sdrtx('Pluto');
txRadio.RadioID = 'usb:0';
txRadio.CenterFrequency = 902e6;
txRadio.BasebandSampleRate = fs;

if isfield(radios, 'Platform')
  radioPlatform = "USRP";
  % Configure USRP radio as the receiver. 
  rxRadio = comm.SDRuReceiver("Platform",radios(1).Platform);
  switch radios(1).Platform
    case {"B200","B210"}
      masterClockRate = 5e6;
      rxRadio.SerialNum = radios(1).SerialNum;
    case {"N200/N210/USRP2"}
      masterClockRate = 100e6;
      rxRadio.IPAddress = radios(1).IPAddress;
    case {"X300","X310"}
      masterClockRate = 200e6;
      rxRadio.IPAddress = radios(1).IPAddress;
  end
  rxRadio.MasterClockRate = masterClockRate;
  rxRadio.DecimationFactor = masterClockRate/fs;
  radioInfo = info(rxRadio);
  maximumGain = radioInfo.MaximumGain;
  minimumGain = radioInfo.MinimumGain;
else
  radioPlatform = "PlutoSDR";
  rxRadio = sdrrx('Pluto');
  rxRadio.RadioID = 'usb:1';
  rxRadio.CenterFrequency = 902e6;
  rxRadio.BasebandSampleRate = fs;
  rxRadio.ShowAdvancedProperties = true;
  rxRadio.EnableQuadratureCorrection = false;
  rxRadio.GainSource = "Manual";
  maximumGain = 73;
  minimumGain = -10;
end
rxRadio.SamplesPerFrame = spf;
% Use burst mode with numFramesInBurst set to 1, so that each capture 
% (call to the receiver) will return an independent fresh frame even 
% though the radio overruns.
rxRadio.EnableBurstMode = true;
rxRadio.NumFramesInBurst = 1;
rxRadio.OutputDataType = 'single';

% Display Tx and Rx radios
txRadio %#ok<NOPRT>
rxRadio %#ok<NOPRT>

% Set random number generator to a known state to be able to regenerate
% the same frames every time the simulation is run
rng(1235)
tic

numModulationTypes = length(modulationTypes);
txModType = repmat(modulationTypes(1),numModulationTypes*numFramesPerModType,1);
estimatedModType = repmat(modulationTypes(1),numModulationTypes*numFramesPerModType,1);
frameCnt = 1;
for modType = 1:numModulationTypes
  elapsedTime = seconds(toc);
  elapsedTime.Format = 'hh:mm:ss';
  fprintf('%s - Testing %s frames\n', ...
    elapsedTime, modulationTypes(modType))
  dataSrc = helperModClassGetSource(modulationTypes(modType), sps, 2*spf, fs);
  modulator = helperModClassGetModulator(modulationTypes(modType), sps, fs);
  if contains(char(modulationTypes(modType)), {'B-FM'})...
           && (radioPlatform == "PlutoSDR")
    % Analog modulation types use a center frequency of 100 MHz
    txRadio.CenterFrequency = 100e6;
    rxRadio.CenterFrequency = 100e6;
  else
    % Digital modulation types use a center frequency of 902 MHz
    txRadio.CenterFrequency = 902e6;
    rxRadio.CenterFrequency = 902e6;
  end
  
  disp('Starting transmitter')
  x = dataSrc();
  y = modulator(x);
  % Remove filter transients
  y = y(4*sps+1:end,1);
  maxVal = max(max(abs(real(y))), max(abs(imag(y))));
  y = y *0.8/maxVal;
  % Download waveform signal to radio and repeatedly transmit it over the air
  transmitRepeat(txRadio, complex(y));
  
  disp('Adjusting receiver gain')
  rxRadio.Gain = maximumGain;
  gainAdjusted = false;
  while ~gainAdjusted
    for p=1:20
      rx = rxRadio();
    end
    maxAmplitude = max([abs(real(rx)); abs(imag(rx))]);
    if (maxAmplitude < 0.8) || (rxRadio.Gain <= minimumGain)
      gainAdjusted = true;
    else
      rxRadio.Gain = rxRadio.Gain - 3;
    end
  end
  
  disp('Starting receiver and test')
  for p=1:numFramesPerModType
    rx = rxRadio();
    
    framePower = mean(abs(rx).^2);
    rx = rx / sqrt(framePower);
    reshapedRx(1,:,1,1) = real(rx);
    reshapedRx(1,:,2,1) = imag(rx);
    
    % Classify
    txModType(frameCnt) = modulationTypes(modType);
    estimatedModType(frameCnt) = classify(trainedNet, reshapedRx);
    
    frameCnt = frameCnt + 1;
    
    % Pause for some time to get an independent channel. The pause duration 
    % together with the processing time of a single loop must be greater 
    % than the channel coherence time. Assume channel coherence time is less 
    % than 0.1 seconds.
    pause(0.1)
  end
  disp('Releasing Tx radio')
  release(txRadio);
  testAccuracy = mean(txModType(1:frameCnt-1) == estimatedModType(1:frameCnt-1));
  disp("Test accuracy: " + testAccuracy*100 + "%")
end
disp('Releasing Rx radio')
release(rxRadio);
testAccuracy = mean(txModType == estimatedModType);
disp("Final test accuracy: " + testAccuracy*100 + "%")

figure
cm = confusionchart(txModType, estimatedModType);
cm.Title = 'Confusion Matrix for Test Data';
cm.RowSummary = 'row-normalized';
cm.Parent.Position = [cm.Parent.Position(1:2) 740 424];
end