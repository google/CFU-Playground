SRC := ${shell find . -type f -name \*.scala}

VERILOGS := VexRiscv_Custom.v VexRiscv_CustomCfu.v VexRiscv_PerfCfu.v VexRiscv_PerfCfuDebug.v VexRiscv_SlimCfu.v VexRiscv_SlimCfuDebug.v VexRiscv_SlimPerfCfu.v VexRiscv_SlimPerfCfuDebug.v VexRiscv_Fomu.v VexRiscv_FomuCfu.v VexRiscv_SlimoptCfu.v VexRiscv_HpsCfu.v VexRiscv_HpsdeltaCfu.v VexRiscv_Fpu.v VexRiscv_FpuCfu.v VexRiscv_MinCfu.v VexRiscv_dbpl8Cfu.v VexRiscv_Breaker.v VexRiscv_BreakerCfu.v
YAMLS    := $(VERILOGS:.v=.yaml)


all: $(VERILOGS)

VexRiscv_Fpu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu false --fpu true --outputFile VexRiscv_Fpu"

VexRiscv_FpuCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu true --fpu true --outputFile VexRiscv_FpuCfu"

VexRiscv_Custom.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu false --outputFile VexRiscv_Custom"

VexRiscv_CustomCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu true --outputFile VexRiscv_CustomCfu"

VexRiscv_dbpl8Cfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu true --dBytesPerLine 8 --outputFile VexRiscv_dbpl8Cfu"

VexRiscv_HpsCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 4096 --csrPluginConfig mcycle --cfu true --cfuRespReadyAlways false --outputFile VexRiscv_HpsCfu"

VexRiscv_HpsdeltaCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 4096 --csrPluginConfig mcycle --cfu true --cfuRespReadyAlways false --outputFile VexRiscv_HpsdeltaCfu"


#================================================================================================
#======== standard CFU models already being used in CFU Playground.   They now live here. =======
#================================================================================================

VexRiscv_MinCfu.v: $(SRC)
	sbt compile "runMain vexriscv.GenCoreDefault --iCacheSize 0 --dCacheSize 0 --csrPluginConfig mcycle --cfu true --mulDiv false --singleCycleShift false --singleCycleMulDiv false --bypass false --prediction none --outputFile VexRiscv_MinCfu"

VexRiscv_PerfCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 8192 --iCacheSize 8192 --csrPluginConfig all --cfu true --perfCSRs 8 --outputFile VexRiscv_PerfCfu"

VexRiscv_PerfCfuDebug.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 8192 --iCacheSize 8192 --csrPluginConfig all -d --cfu true --perfCSRs 8 --outputFile VexRiscv_PerfCfuDebug"

VexRiscv_SlimoptCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 4096 --csrPluginConfig all --cfu true --cfuRespReadyAlways true --outputFile VexRiscv_SlimoptCfu"

VexRiscv_SlimCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu true --outputFile VexRiscv_SlimCfu"

VexRiscv_SlimCfuDebug.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all -d --cfu true --outputFile VexRiscv_SlimCfuDebug"

VexRiscv_SlimPerfCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu true --perfCSRs 8 --outputFile VexRiscv_SlimPerfCfu"

VexRiscv_SlimPerfCfuDebug.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all -d --cfu true --perfCSRs 8 --outputFile VexRiscv_SlimPerfCfuDebug"

VexRiscv_Fomu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --safe false --iCacheSize 2048 --dCacheSize 0 --csrPluginConfig mcycle --mulDiv true --singleCycleShift false --singleCycleMulDiv true --bypass false --prediction none --hardwareDiv false --outputFile VexRiscv_Fomu"

VexRiscv_FomuCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --safe false --cfu true --iCacheSize 2048 --dCacheSize 0 --csrPluginConfig mcycle --mulDiv true --singleCycleShift false --singleCycleMulDiv true --bypass false --prediction none --hardwareDiv false --outputFile VexRiscv_FomuCfu"

VexRiscv_Breaker.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --safe false --cfu false --iCacheSize 2048 --dCacheSize 0 --csrPluginConfig mcycle --mulDiv true --singleCycleShift true --singleCycleMulDiv false --bypass true --prediction dynamic --hardwareDiv false --outputFile VexRiscv_Breaker"

VexRiscv_BreakerCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.GenCoreDefault --safe false --cfu true --iCacheSize 2048 --dCacheSize 0 --csrPluginConfig mcycle --mulDiv true --singleCycleShift true --singleCycleMulDiv false --bypass true --prediction dynamic --hardwareDiv false --outputFile VexRiscv_BreakerCfu"
