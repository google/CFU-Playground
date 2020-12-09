# Makefile reusing as much from the LiteX gateware and software builds as possible.

PROJ_DIR   := $(abspath ..)
PROJ       := $(lastword $(subst /, ,$(PROJ_DIR)))
PLATFORM   := arty.$(PROJ)

# These are found in the PATH
RV64       := riscv64-unknown-elf-
# RV64       := riscv64-elf-
CC         := $(RV64)gcc
CXX        := $(RV64)g++
OBJCOPY    := $(RV64)objcopy
OBJDUMP    := $(RV64)objdump

RM         := rm -rf
COPY       := cp -a
PATH_SEP   := /

# Assumes current directory is the one containing the makefile
BASE_DIR   := .
CFU_DIR    := $(BASE_DIR)/../../..
SOC_DIR    := $(CFU_DIR)/soc
BUILD_DIR  := $(SOC_DIR)/build/$(PLATFORM)/software
LITEX_DIR  := $(SOC_DIR)/deps/litex/litex
VEX_SRC_DIR  := $(LITEX_DIR)/soc/cores/cpu/vexriscv
LXTERM     := $(SOC_DIR)/bin/litex_term

LD_DIR     := $(BASE_DIR)/ld
GEN_LD_DIR := $(BUILD_DIR)/include/generated
LDSCRIPT   := $(LD_DIR)/linker.ld
LDSCRIPTS  := $(LDSCRIPT) $(GEN_LD_DIR)/output_format.ld $(GEN_LD_DIR)/regions.ld

SRC_DIR     := $(BASE_DIR)/src
THIRD_PARTY := $(PROJ_DIR)/third_party

# TODO: always do or always don't debug build
DBG_CFLAGS := -ggdb -g -DDEBUG -Wall
DBG_LFLAGS := -ggdb -g -Wall
DBG_LFLAGS := 

PACKAGE    := basic


CFLAGS     := \
	-ggdb -g -DDEBUG -Wall \
	-I$(BASE_DIR)/include -D__vexriscv__ -march=rv32im  -mabi=ilp32 \
	-I$(BUILD_DIR)/include \
	-I$(THIRD_PARTY)/include \
	-I$(BASE_DIR)/.. \
	-I$(LITEX_DIR)/soc/software/include/base \
	-I$(LITEX_DIR)/soc/software/include \
	-I$(VEX_SRC_DIR) \
	-fno-builtin -nostdinc \
	-Wall -Wextra \
	-ffunction-sections -fdata-sections -fno-common \
	-fomit-frame-pointer \
	-march=rv32im \
	-std=gnu11 \
	-O2 
	# -Os 
CXXFLAGS   := $(CFLAGS) -std=c++11 -fno-rtti -fno-exceptions

LFLAGS     := $(CFLAGS) \
	-L$(LD_DIR) \
	-L$(GEN_LD_DIR) \
	-L$(BUILD_DIR)/libbase -lbase-nofloat \
	-L$(BUILD_DIR)/libcompiler_rt -lcompiler_rt \
	-nostdlib -nodefaultlibs \
	-nostartfiles \
	-Wl,--gc-sections \
	-Wl,--no-warn-mismatch \
	-Wl,--script=$(LDSCRIPT) \
	-Wl,--build-id=none

OBJ_DIR    := .obj

CSOURCES   := $(wildcard $(SRC_DIR)/*.c)
CPPSOURCES := $(wildcard $(SRC_DIR)/*.cpp)
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

info:
	echo Dir:
	ls -lstr $(LITEX_DIR)/soc/software/include/base

$(OBJECTS): | $(OBJ_DIR)

$(TARGET): $(OBJECTS) $(LDSCRIPTS)
	$(QUIET) echo "  LD       $@"
	$(QUIET) $(CC) $(OBJECTS) $(LFLAGS) -o $@
	$(QUIET) echo "  OBJDUMP  $@"
	$(QUIET) $(OBJDUMP) -d $@ > $@.dis
	$(QUIET) $(OBJDUMP) -t $@ > $@.sym

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

clean:
	$(QUIET) echo "  RM      $(subst /,$(PATH_SEP),$(wildcard $(OBJ_DIR)/*.d))"
	-$(QUIET) $(RM) $(subst /,$(PATH_SEP),$(wildcard $(OBJ_DIR)/*.d))
	$(QUIET) echo "  RM      $(subst /,$(PATH_SEP),$(wildcard $(OBJ_DIR)/*.o))"
	-$(QUIET) $(RM) $(subst /,$(PATH_SEP),$(wildcard $(OBJ_DIR)/*.o))
	$(QUIET) echo "  RM      $(TARGET) $(PACKAGE).bin $(PACKAGE).symbol $(PACKAGE).ihex $(TARGET).sym $(TARGET).dis"
	-$(QUIET) $(RM) $(TARGET) $(PACKAGE).bin $(PACKAGE).symbol $(PACKAGE).ihex $(TARGET).sym $(TARGET).dis

include $(wildcard $(OBJ_DIR)/*.d)

run:
	$(LXTERM) --speed 115200 --kernel basic.bin /dev/ttyUSB?


.PHONY: clean prog 
