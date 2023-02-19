function flag = parallelComputingLicenseExists()
%parallelComputingLicenseExists Check Parallel Computing Toolbox availability
%   L = parallelComputingLicenseExists returns true, if Parallel Computing
%   Toolbox is installed and license is available. Otherwise, this function
%   returns false.
%
%   See also LLRNeuralNetworkExample.

%   Copyright 2019 The MathWorks, Inc.

flag = license('test', 'distrib_computing_toolbox') && ...
  (exist('gcp','file') == 2);
end