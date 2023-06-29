function flag = helperIsUSRPInstalled
%helperIsUSRPInstalled Check if USRP Radio HSP is installed

spkg = matlabshared.supportpkg.getInstalled;
flag = ~isempty(spkg) && any(contains({spkg.Name},'USRP','IgnoreCase',true));
end