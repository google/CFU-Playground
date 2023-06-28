classdef helperModClassTestChannel < matlab.System
%helperModClassTestChannel Test channel for modulation classification
%   CH = helperModClassTestChannel creates an channel System object, CH.
%   This object adds multipath fading, clock offset effects, and white
%   Gaussian noise to a framed signal.
%   
%   CH = helperModClassTestChannel(Name,Value) creates a channel object,
%   CH, with the specified property Name set to the specified Value. You
%   can specify additional name-value pair arguments in any order as
%   (Name1,Value1,...,NameN,ValueN).
%   
%   The channel object uses the default MATLAB random stream. Reset the
%   default stream for repeatable simulations. Type 'help RandStream' for
%   more information.
%   
%   Step method syntax:
%   
%   Y = step(CH,X) adds multipath fading, clock offset effects, and white
%   Gaussian noise to input X and returns the result in Y. The input X must
%   be a double or single precision data type column vector. Each frame is
%   impaired with an independent channel. The channel applies following
%   impairments in the given order:
%
%   1) Add Rician multipath fading to input, X, based on PathDelays,
%   AveragePathGains, KFactor, and MaximumDopplerShift settings. Channel
%   path gains are regenerated for each frame, which provides independent
%   path gain values for each frame.
%
%   2) Add clock offset effects.
%     a) Frequency offset, which is determined by the clock offset (ppm)
%     and the center frequency, as fOffset = -(C-1)*fc, where fc is the
%     center frequency in Hz and C is the clock offset factor. clock offset
%     factor, C, is calculated as C = (1+offset/1e6), where offset is the
%     clock offset in ppm.
%     b) Sampling offset, which is determined by the clock offset (ppm) and
%     sampling rate, fs. This method first generates a clock offset value,
%     offset, in ppm, based on the specified maximum clock offset and
%     calculates the offset factor, C, as C = (1+offset/1e6), where offset
%     is the clock offset in ppm. The signal is resampled using interp1
%     function at a new sampling rate of C*fs.
%
%   3) Add Gaussian noise based on the specified SNR value. Channel object,
%   CH, assumes that the input signal is normalized to unity power.
%   
%   System objects may be called directly like a function instead of using
%   the step method. For example, y = step(obj, x) and y = obj(x) are
%   equivalent.
%
%   helperModClassTestChannel methods:
%   
%   step     - Add channel impairments to input signal (see above)
%   release  - Allow property value and input characteristics changes
%   clone    - Create a channel object with same property values
%   isLocked - Locked status (logical)
%   reset    - Reset channel object
%   
%   helperModClassTestChannel properties:
%   
%   SNR                  - SNR (dB)
%   CenterFrequency      - Center frequency (Hz)
%   SampleRate           - Input signal sample rate (Hz)
%   PathDelays           - Discrete path delay vector (s)
%   AveragePathGains     - Average path gain vector (dB)
%   KFactor              - Rician K-factor (linear scale)
%   MaximumDopplerShift  - Maximum Doppler shift (Hz)
%   MaximumClockOffset   - Maximum clock offset (ppm)
%   
%   See also ModulationClassificationWithDeepLearningExample.
 
%   Copyright 2018 The MathWorks, Inc.

  properties
    %SNR      SNR (dB)    
    %   Specify the SNR value in decibels. Set this property to a numeric,
    %   real scalar. The default is 20 dB. This property is tunable.
    SNR = 20
    %CenterFrequency Center frequency (Hz)
    %   Specify the center frequency as a double precision nonnegative
    %   scalar. The default is 2.4 GHz. Center frequency value is used to
    %   calculate expected frequency offset in the received signal based on
    %   the maximum clock offset value. This property is tunable.
    CenterFrequency = 2.4e9
  end

  properties (Nontunable)
    %SampleRate Sample rate (Hz)
    %   Specify the sample rate of the input signal in Hz as a double
    %   precision, real, positive scalar. The default is 1 Hz.
    SampleRate = 1
    %PathDelays Discrete path delays (s)
    %   Specify the delays of the discrete paths in seconds as a double
    %   precision, real, scalar or row vector. When PathDelays is a scalar,
    %   the channel is frequency-flat; When PathDelays is a vector, the
    %   channel is frequency-selective. The default is 0.
    PathDelays = 0
    %AveragePathGains Average path gains (dB)
    %   Specify the average gains of the discrete paths in dB as a double
    %   precision, real, scalar or row vector. AveragePathGains must have
    %   the same size as PathDelays. The default is 0.
    AveragePathGains = 0
    %KFactor K-factors
    %   Specify the K factor of a Rician fading channel as a double
    %   precision, real, positive scalar. The first discrete path is a
    %   Rician fading process with a Rician K-factor of KFactor and the
    %   remaining discrete paths are independent Rayleigh fading processes.
    %   The default is 3.
    KFactor = 3
    %MaximumDopplerShift Maximum Doppler shift (Hz)
    %   Specify the maximum Doppler shift for the path(s) of the channel in
    %   Hz as a double precision, real, nonnegative scalar. It applies to
    %   all the paths of the channel. When MaximumDopplerShift is 0, the
    %   channel is static for the entire input and you can use the reset
    %   method to generate a new channel realization. The
    %   MaximumDopplerShift must be smaller than SampleRate/10 for each
    %   path. The default is 0.
    MaximumDopplerShift = 0
    %MaximumClockOffset Maximum clock offset (ppm)
    %   Specify the maximum clock offset in ppm as a double precision,
    %   real, non-negative scalar. Channel generates a uniformly
    %   distributed random clock offset value between -MaximumClockOffset
    %   and MaximumClockOffset for each frame. This clock offset value is
    %   used to calculate frequency and timing offset for the current
    %   frame. The default is 0.
    MaximumClockOffset = 0
  end

  properties(Access = private)
    MultipathChannel
    FrequencyShifter
    TimingShifter
    C % 1+(ppm/1e6)
  end

  methods
    function obj = helperModClassTestChannel(varargin)
      % Support name-value pair arguments when constructing object
      setProperties(obj,nargin,varargin{:})
    end
  end
  
  methods(Access = protected)
    function setupImpl(obj)
      obj.MultipathChannel = comm.RicianChannel(...
        'SampleRate', obj.SampleRate, ...
        'PathDelays', obj.PathDelays, ...
        'AveragePathGains', obj.AveragePathGains, ...
        'KFactor', obj.KFactor, ...
        'MaximumDopplerShift', obj.MaximumDopplerShift);
      obj.FrequencyShifter = comm.PhaseFrequencyOffset(...
        'SampleRate', obj.SampleRate);
    end

    function y = stepImpl(obj,x)
      % Add channel impairments
      
      yInt1 = addMultipathFading(obj,x);
      yInt2 = addClockOffset(obj, yInt1);
      y     = addNoise(obj, yInt2);
    end

    function out = addMultipathFading(obj, in)
      %addMultipathFading Add Rician multipath fading
      %   Y=addMultipathFading(CH,X) adds Rician multipath fading effects
      %   to input, X, based on PathDelays, AveragePathGains, KFactor, and
      %   MaximumDopplerShift settings. Channel path gains are regenerated
      %   for each frame, which provides independent path gain values for
      %   each frame.
      
      % Get new path gains
      reset(obj.MultipathChannel)
      % Pass input through the new channel
      out = obj.MultipathChannel(in);
    end
    
    function out = addClockOffset(obj, in)
      %addClockOffset Add effects of clock offset
      %   Y=addClockOffset(CH,X) adds effects of clock offset. Clock offset
      %   has two effects on the received signal: 1) Frequency offset,
      %   which is determined by the clock offset (ppm) and the carrier
      %   frequency; 2) Sampling time drift, which is determined by the
      %   clock offset (ppm) and sampling rate. This method first generates
      %   a clock offset value in ppm, based on the specified maximum clock
      %   offset and calculates the offset factor, C, as
      %   
      %   C = (1+offset/1e6), where offset is the clock offset in ppm.
      %
      %   applyFrequencyOffset and applyTimingDrift add frequency offset
      %   and sampling time drift to the signal, respectively.
      
      % Determine clock offset factor
      maxOffset = obj.MaximumClockOffset;
      clockOffset = (rand() * 2*maxOffset) - maxOffset;
      obj.C = 1 + clockOffset / 1e6;
      
      % Add frequency offset
      outInt1 = applyFrequencyOffset(obj, in);

      % Add sampling time drift
      out = applyTimingDrift(obj, outInt1);
    end
    
    function out = applyFrequencyOffset(obj, in)
      %applyFrequencyOffset Apply frequency offset
      %   Y=applyFrequencyOffset(CH,X) applies frequency offset to input,
      %   X, based on the clock offset for the current frame and center
      %   frequency. 
      %
      %   fOffset = -(C-1)*fc, where fc is center frequency in Hz
      %   y = x .* exp(1i*2*pi*fOffset*t)
      
      obj.FrequencyShifter.FrequencyOffset = ...
        -(obj.C-1)*obj.CenterFrequency;
      out = obj.FrequencyShifter(in);
    end
    
    function out = applyTimingDrift(obj, in)
      %applyTimingDrift Apply sampling time drift
      %   Y=applyTimingDrift(CH,X) applies sampling time drift to
      %   input, X, based on the clock offset for the current frame and
      %   specified sampling rate, Fs. X is resampled at C*Fs Hz using
      %   linear interpolation.
      
      originalFs = obj.SampleRate;
      x = (0:length(in)-1)' / originalFs;
      newFs = originalFs * obj.C;
      xp = (0:length(in)-1)' / newFs;
      out = interp1(x, in, xp);
    end
    
    function out = addNoise(obj, in)
      %addNoise Add Gaussian noise
      %   Y=addNoise(CH,X) adds Gaussian noise to input, X, based on the
      %   specified SNR value. Channel object, CH, assumes that the input
      %   signal is normalized to unity power.
      out = awgn(in,obj.SNR);
    end
    
    function resetImpl(obj)
      reset(obj.MultipathChannel);
      reset(obj.FrequencyShifter);
    end

    function s = infoImpl(obj)
      if isempty(obj.MultipathChannel)
        setupImpl(obj);
      end
      
      % Get channel delay from fading channel object delay
      mpInfo = info(obj.MultipathChannel);
      
      % Calculate maximum frequency offset
      maxClockOffset = obj.MaximumClockOffset;
      maxFreqOffset = (maxClockOffset / 1e6) * obj.CenterFrequency;
      
      % Calculate maximum timing offset
      maxClockOffset = obj.MaximumClockOffset;
      maxSampleRateOffset = (maxClockOffset / 1e6) * obj.SampleRate;
      
      s = struct('ChannelDelay', ...
        mpInfo.ChannelFilterDelay, ...
        'MaximumFrequencyOffset', maxFreqOffset, ...
        'MaximumSampleRateOffset', maxSampleRateOffset);
    end
  end
end
