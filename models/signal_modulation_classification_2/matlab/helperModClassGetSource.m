function src = helperModClassGetSource(modType, sps, spf, fs)
%helperModClassGetSource Source selector for modulation types
%    SRC = helperModClassGetSource(TYPE,SPS,SPF,FS) returns the data source
%    for the modulation type TYPE, with the number of samples per symbol
%    SPS, the number of samples per frame SPF, and the sampling frequency
%    FS.
%   
%   See also ModulationClassificationWithDeepLearningExample.

%   Copyright 2019 The MathWorks, Inc.

switch modType
  case {"BPSK","GFSK","CPFSK"}
    M = 2;
    src = @()randi([0 M-1],spf/sps,1);
  case {"QPSK","PAM4"}
    M = 4;
    src = @()randi([0 M-1],spf/sps,1);
  case "8PSK"
    M = 8;
    src = @()randi([0 M-1],spf/sps,1);
  case "16QAM"
    M = 16;
    src = @()randi([0 M-1],spf/sps,1);
  case "64QAM"
    M = 64;
    src = @()randi([0 M-1],spf/sps,1);
  case {"B-FM","DSB-AM","SSB-AM"}
    src = @()getAudio(spf,fs);
end
end

function x = getAudio(spf,fs)
%getAudio Audio source for analog modulation types
%    A = getAudio(SPF,FS) returns the audio source A, with the
%    number of samples per frame SPF, and the sample rate FS.

persistent audioSrc audioRC

if isempty(audioSrc)
  audioSrc = dsp.AudioFileReader('audio_mix_441.wav',...
    'SamplesPerFrame',spf,'PlayCount',inf);
  audioRC = dsp.SampleRateConverter('Bandwidth',30e3,...
    'InputSampleRate',audioSrc.SampleRate,...
    'OutputSampleRate',fs);
  [~,decimFactor] = getRateChangeFactors(audioRC);
  audioSrc.SamplesPerFrame = ceil(spf / fs * audioSrc.SampleRate / decimFactor) * decimFactor;
end

x = audioRC(audioSrc());
x = x(1:spf,1);
end