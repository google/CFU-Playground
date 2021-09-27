SRC := ${shell find . -type f -name \*.scala}

VERILOGS := VexRiscv_Custom.v VexRiscv_CustomCfu.v
YAMLS    := $(VERILOGS:.v=.yaml)


all: $(VERILOGS)

VexRiscv_Custom.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.Custom --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu false --outputFile $@"

VexRiscv_CustomCfu.v: $(SRC) Makefile
	sbt compile "runMain vexriscv.Custom --dCacheSize 4096 --iCacheSize 2048 --csrPluginConfig all --cfu true --outputFile $@"
