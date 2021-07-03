# Makefile reusing as much from the LiteX gateware and software builds as possible.
ifndef CFU_ROOT
$(error CFU_ROOT not set)
endif

ifndef PROJ
$(error PROJ not set)
endif

ifndef SOC_SOFTWARE_DIR
$(error SOC_SOFTWARE_DIR not set)
endif

# These are found in the PATH
RV64       := riscv64-unknown-elf-
CC         := $(RV64)gcc
CXX        := $(RV64)g++
OBJDUMP    := $(RV64)objdump
OBJCOPY    := $(RV64)objcopy

RM         := rm -rf
COPY       := cp -a
PATH_SEP   := /

# Assumes current directory is the one containing the makefile
BUILD_DIR      := $(abspath .)
LIBBASE_DIR    := $(SOC_SOFTWARE_DIR)/libbase
LITEX_DIR      := $(CFU_ROOT)/third_party/python/litex/litex
VEX_SRC_DIR    := $(LITEX_DIR)/soc/cores/cpu/vexriscv
PYRUN          := $(CFU_ROOT)/scripts/pyrun
FIX_CFU_DIS    := $(PYRUN) $(CFU_ROOT)/scripts/fix_cfu_dis.py
XXD            := $(PYRUN) $(CFU_ROOT)/scripts/xxd.py

LD_DIR     := $(BUILD_DIR)/ld
GEN_LD_DIR := $(SOC_SOFTWARE_DIR)/include/generated
LDSCRIPT   := $(LD_DIR)/linker.ld
LDSCRIPTS  := $(LDSCRIPT) $(GEN_LD_DIR)/output_format.ld $(GEN_LD_DIR)/regions.ld

SRC_DIR    := $(BUILD_DIR)/src

PACKAGE    := software

DEFINE_FLAGS := $(DEFINES:%=-D %)

SHARED_FLAGS := \
	-march=rv32im  \
	-mabi=ilp32 \
	-D__vexriscv__ \
	$(DEFINE_FLAGS) \
	-I$(SRC_DIR) \
	-I$(SRC_DIR)/third_party/gemmlowp \
	-I$(SRC_DIR)/third_party/flatbuffers/include \
	-I$(SRC_DIR)/third_party/ruy \
	-I$(SRC_DIR)/third_party/kissfft \
	-I$(SOC_SOFTWARE_DIR)/include \
	-ffunction-sections \
	-fdata-sections \
	-fno-common \
	-fomit-frame-pointer \
	-ffreestanding \
	-Werror\
	-Wsign-compare\
	-Wdouble-promotion\
	-Wshadow\
	-Wunused-variable\
	-Wmissing-field-initializers\
	-Wunused-function\
	-Wswitch\
	-Wvla\
	-DTF_LITE_STATIC_MEMORY\
	-DTF_LITE_USE_GLOBAL_CMATH_FUNCTIONS\
	-DTF_LITE_USE_GLOBAL_MIN\
	-DTF_LITE_USE_GLOBAL_MAX \
	-DTF_LITE_DISABLE_X86_NEON\
	-g \
	-O3 \
	-fno-builtin 
	
CFLAGS  := \
	$(SHARED_FLAGS)\
	-I$(LITEX_DIR)/soc/software/include/base \
	-I$(LITEX_DIR)/soc/software/include \
	-I$(VEX_SRC_DIR) 

CXXFLAGS   := \
	$(SHARED_FLAGS) \
	-std=c++11 \
	-fstrict-aliasing \
	-fno-rtti \
	-fno-exceptions \
	-fno-threadsafe-statics\
	-fmessage-length=0 \
	-Wall \
	-Wextra \
	-Wstrict-aliasing \
	-Wno-unused-parameter

LFLAGS     := \
	$(CXXFLAGS) \
	-L$(LD_DIR) \
	-L$(GEN_LD_DIR) \
	-L$(SOC_SOFTWARE_DIR)/libbase -lbase-nofloat \
	-L$(SOC_SOFTWARE_DIR)/libcompiler_rt -lcompiler_rt \
	-lm \
	-nostartfiles \
	-Wl,--gc-sections \
	-Wl,--fatal-warnings \
	-Wl,--no-warn-mismatch \
	-Wl,--script=$(LDSCRIPT) \
	-Wl,--build-id=none 
	

find_srcs = $(shell find $(SRC_DIR) -name \*.$(1))
CSOURCES   := $(call find_srcs,c) 
CPPSOURCES := $(call find_srcs,cpp)
CCSOURCES  := $(call find_srcs,cc) 
ASOURCES   := $(call find_srcs,S) 
MODEL_SRCS := $(call find_srcs,tflite)
DATA_SRCS  := $(call find_srcs,dat)

COBJS      := $(CSOURCES:.c=.o)
CXXOBJS    := $(CPPSOURCES:.cpp=.o) $(CCSOURCES:.cc=.o) 
AOBJS      := $(ASOURCES:.S=.o)
OBJECTS    := $(COBJS) $(CXXOBJS) $(AOBJS)
MODEL_INCS := $(MODEL_SRCS:.tflite=.h)
DATA_INCS  := $(DATA_SRCS:.dat=.h)

ifdef V
QUIET      :=
else
QUIET      := @
endif

TARGET := $(PACKAGE).elf

.PHONY: all
all: $(TARGET) $(PACKAGE).bin $(PACKAGE).ihex

$(PACKAGE).bin: $(TARGET)	
	$(QUIET) echo "  OBJCOPY  $@"
	$(QUIET) $(OBJCOPY) -O binary $(TARGET) $@

$(PACKAGE).ihex: $(TARGET)
	$(QUIET) echo "  IHEX     $(PACKAGE).ihex"
	$(QUIET) $(OBJCOPY) -O ihex $(TARGET) $@

$(TARGET): $(OBJECTS) $(LDSCRIPTS)
	$(QUIET) echo "  LD       $@"
	$(QUIET) $(CXX) $(OBJECTS) $(LFLAGS) -o $@
	$(QUIET) echo "  OBJDUMP  $@.dis"
	$(QUIET) $(OBJDUMP) -d -S -l $(TARGET) | $(FIX_CFU_DIS) > $(TARGET).dis_with_source
	$(QUIET) $(OBJDUMP) -d $(TARGET) | $(FIX_CFU_DIS) > $(TARGET).dis
	$(QUIET) echo "  OBJDUMP  $@.sym"
	$(QUIET) $(OBJDUMP) -s $(TARGET) > $(TARGET).sym

%.h : %.tflite
	$(QUIET) echo "  XXD  $(notdir $<) $(notdir $@)"
	$(QUIET) $(XXD) $< $@

%.h : %.dat
	$(QUIET) echo "  XXD  $(notdir $<) $(notdir $@)"
	$(QUIET) $(XXD) $< $@
	
 
# Some shenanigans to create a file whose name depends on compiler DEFINEs
# We use this to cause a rebuild when DEFINEs change. See
# https://stackoverflow.com/questions/11647859/make-targets-depend-on-variables
DEFINE_FILE = DEFINES.$(firstword $(shell echo $(DEFINES) | md5sum))
$(DEFINE_FILE):
	$(QUIET) $(RM) DEFINES.*
	echo $(DEFINES) > $(DEFINE_FILE)

# Force model include files to be generated first
$(OBJECTS): | $(MODEL_INCS) $(DATA_INCS)

%.o : %.c $(DEFINE_FILE)
	$(QUIET) echo "  CC  $(notdir $<)	$(notdir $@)"
	$(QUIET) $(CC) -c $< $(CFLAGS) -o $@ -MMD

%.o: %.cpp $(DEFINE_FILE)
	$(QUIET) echo "  CXX $(notdir $<)	$(notdir $@)"
	$(QUIET) $(CXX) -DREPLACE_NAME_=$(notdir $*) -c $< $(CXXFLAGS) -o $@ -MMD

%.o: %.cc $(DEFINE_FILE)
	$(QUIET) echo "  CXX $(notdir $<)	$(notdir $@)"
	$(QUIET) $(CXX) -DREPLACE_NAME_=$(notdir $*) -c $< $(CXXFLAGS) -o $@ -MMD

%.o : %.S $(DEFINE_FILE)
	$(QUIET) echo "  AS  $(notdir $<)	$(notdir $@)"
	$(QUIET) $(CC) -x assembler-with-cpp -c $< $(CFLAGS) -o $@ -MMD

include $(shell find src -name *.d)
