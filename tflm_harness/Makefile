# Makefile reusing as much from the LiteX gateware and software builds as possible.

PLATFORM   := arty
MODEL      ?= pdti8

# These are found in the PATH
RV64       := riscv64-unknown-elf-
CC         := $(RV64)gcc
CXX        := $(RV64)g++
OBJDUMP    := $(RV64)objdump
OBJCOPY    := $(RV64)objcopy

RM         := rm -rf
COPY       := cp -a
XXD        := xxd -i
PATH_SEP   := /

# Assumes current directory is the one containing the makefile
BASE_DIR   := .
CFU_ROOT   := ..
SOC_DIR    := $(CFU_ROOT)/soc
BUILD_DIR  := $(SOC_DIR)/build/$(PLATFORM)/software
LITEX_DIR  := $(SOC_DIR)/deps/litex/litex
VEX_SRC_DIR  := $(LITEX_DIR)/soc/cores/cpu/vexriscv

MODELS_DIR := $(CFU_ROOT)/models
MODEL_FB   := $(MODELS_DIR)/$(MODEL)/$(MODEL).tflite
MODEL_LN   := model.tflite
MODEL_C    := $(BASE_DIR)/$(MODEL)_tflite.c

LD_DIR     := $(BASE_DIR)/ld
GEN_LD_DIR := $(BUILD_DIR)/include/generated
LDSCRIPT   := $(LD_DIR)/linker.ld
LDSCRIPTS  := $(LDSCRIPT) $(GEN_LD_DIR)/output_format.ld $(GEN_LD_DIR)/regions.ld

SRC_DIR    := $(BASE_DIR)/src
THIRD_PARTY := $(CFU_ROOT)/third_party
TFLM_DIR   := $(THIRD_PARTY)/tflm_gen
TFLM_LIB   := $(TFLM_DIR)/libtensorflow-microlite.a

# TODO: always do or always don't debug build
DBG_CFLAGS := -ggdb -g -DDEBUG -Wall
DBG_LFLAGS := -ggdb -g -Wall

PACKAGE    := tflm_harness


SHARED_FLAGS := \
	-march=rv32im  -mabi=ilp32 \
	-I$(BASE_DIR)/include -D__vexriscv__ \
	-I$(TFLM_DIR) \
	-I$(TFLM_DIR)/third_party/gemmlowp \
	-I$(TFLM_DIR)/third_party/flatbuffers/include \
	-I$(TFLM_DIR)/third_party/ruy \
	-I$(BUILD_DIR)/include \
	-ffunction-sections -fdata-sections -fno-common \
	-fomit-frame-pointer \
	-Werror\
	-Wsign-compare\
	-Wdouble-promotion\
	-Wshadow\
	-Wunused-variable\
	-Wmissing-field-initializers\
	-Wunused-function\
	-Wswitch\
	-Wvla\
	-DNDEBUG\
	-DTF_LITE_STATIC_MEMORY\
	-DTF_LITE_USE_GLOBAL_CMATH_FUNCTIONS\
	-DTF_LITE_USE_GLOBAL_MIN\
	-DTF_LITE_USE_GLOBAL_MAX \
	-DTF_LITE_DISABLE_X86_NEON\
	-O2 

CFLAGS  := \
	$(SHARED_FLAGS)\
	-I$(LITEX_DIR)/soc/software/include/base \
	-I$(LITEX_DIR)/soc/software/include \
	-I$(VEX_SRC_DIR) \
	-fno-builtin 


CXXFLAGS   := \
	$(SHARED_FLAGS) \
	-std=c++11 \
	-fstrict-aliasing \
	-fno-rtti \
	-fno-exceptions \
	-fno-threadsafe-statics

LFLAGS     := $(CFLAGS) \
	-L$(LD_DIR) \
	-L$(GEN_LD_DIR) \
	-L$(BUILD_DIR)/libbase -lbase-nofloat \
	-L$(BUILD_DIR)/libcompiler_rt -lcompiler_rt \
	-L$(TFLM_DIR) -ltensorflow-microlite \
	-lm \
	-nostartfiles \
	-Wl,--gc-sections \
	-Wl,--no-warn-mismatch \
	-Wl,--script=$(LDSCRIPT) \
	-Wl,--build-id=none

OBJ_DIR    := .obj

CSOURCES   := $(wildcard $(SRC_DIR)/*.c   ) $(MODEL_C)
CPPSOURCES := $(wildcard $(SRC_DIR)/*.cpp )
ASOURCES   := $(wildcard $(SRC_DIR)/*.S)

# All the object files go in OBJ_DIR, but putting them there causes us to lose
# the path to the source files. Setting VPATH allows Make to search for the
# source files based on the object file name. #hack
VPATH      := $(SRC_DIR)
COBJS      := $(addprefix $(OBJ_DIR)/, $(notdir $(CSOURCES:.c=.o)))
CXXOBJS    := $(addprefix $(OBJ_DIR)/, $(notdir $(CPPSOURCES:.cpp=.o)))
AOBJS      := $(addprefix $(OBJ_DIR)/, $(notdir $(ASOURCES:.S=.o)))
OBJECTS    := $(COBJS) $(CXXOBJS) $(AOBJS)


ifdef V
QUIET      :=
else
QUIET      := @
endif

ALL        := all
TARGET     := $(PACKAGE).elf
CLEAN      := clean

all: $(TARGET) $(PACKAGE).bin $(PACKAGE).ihex

$(OBJECTS): | $(OBJ_DIR)

#
# Use a symbolic link to get consistent variable names
#
$(MODEL_C): $(MODEL_FB)
	-$(QUIET) /bin/rm -f $(MODEL_LN)
	$(QUIET) ln -s $< $(MODEL_LN)
	$(QUIET) echo "  XXD      $<	$(notdir $@)"
	$(QUIET) $(XXD) $(MODEL_LN) > $@

$(TFLM_LIB):
	$(QUIET) echo "  MAKE     $@"
	$(QUIET) $(MAKE) -j -C $(TFLM_DIR) $(notdir $(TFLM_LIB))

$(TARGET): $(OBJECTS) $(TFLM_LIB) $(LDSCRIPTS)
	$(QUIET) echo "  LD       $@"
	$(QUIET) $(CC) $(OBJECTS) $(LFLAGS) -o $@
	$(QUIET) echo "  OBJDUMP  $@.dis"
	$(QUIET) $(OBJDUMP) -d $(TARGET) > $(TARGET).dis
	$(QUIET) echo "  OBJDUMP  $@.sym"
	$(QUIET) $(OBJDUMP) -s $(TARGET) > $(TARGET).sym


$(PACKAGE).bin: $(TARGET)
	$(QUIET) echo "  OBJCOPY  $@"
	$(QUIET) $(OBJCOPY) -O binary $(TARGET) $@

$(PACKAGE).ihex: $(TARGET)
	$(QUIET) echo "  IHEX     $(PACKAGE).ihex"
	$(QUIET) $(OBJCOPY) -O ihex $(TARGET) $@

$(DEBUG): CFLAGS += $(DBG_CFLAGS)
$(DEBUG): LFLAGS += $(DBG_LFLAGS)
CFLAGS += $(DBG_CFLAGS)
LFLAGS += $(DBG_LFLAGS)
$(DEBUG): $(TARGET)

$(OBJ_DIR):
	$(QUIET) mkdir $(OBJ_DIR)

$(COBJS) : $(OBJ_DIR)/%.o : %.c $(BASE_DIR)/Makefile
	$(QUIET) echo "  CC       $<	$(notdir $@)"
	$(QUIET) $(CC) -c $< $(CFLAGS) -o $@ -MMD

$(OBJ_DIR)/%.o: %.cpp
	$(QUIET) echo "  CXX      $<	$(notdir $@)"
	$(QUIET) $(CXX) -c $< $(CXXFLAGS) -o $@ -MMD

$(AOBJS) : $(OBJ_DIR)/%.o : %.S
	$(QUIET) echo "  AS       $<	$(notdir $@)"
	$(QUIET) $(CC) -x assembler-with-cpp -c $< $(CFLAGS) -o $@ -MMD

renode:
	renode -e "i @litex-vexriscv-tflite.resc"


clean:
	$(QUIET) echo "  RM      $(subst /,$(PATH_SEP),$(wildcard $(OBJ_DIR)/*.d))"
	-$(QUIET) $(RM) $(subst /,$(PATH_SEP),$(wildcard $(OBJ_DIR)/*.d))
	$(QUIET) echo "  RM      $(subst /,$(PATH_SEP),$(wildcard $(OBJ_DIR)/*.d))"
	-$(QUIET) $(RM) $(subst /,$(PATH_SEP),$(wildcard $(OBJ_DIR)/*.o))
	$(QUIET) echo "  RM      $(TARGET) $(PACKAGE).bin $(PACKAGE).symbol $(PACKAGE).ihex $(TARGET).dis $(TARGET).sym"
	-$(QUIET) $(RM) $(TARGET) $(PACKAGE).bin $(PACKAGE).symbol $(PACKAGE).ihex $(TARGET).dis $(TARGET).sym
	$(QUIET) $(MAKE) -C $(TFLM_DIR) clean

include $(wildcard $(OBJ_DIR)/*.d)

.PHONY: clean prog 
