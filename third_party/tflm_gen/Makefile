TARGET_TOOLCHAIN_ROOT := 
TARGET_TOOLCHAIN_PREFIX := riscv32-unknown-elf-
TARGET_TOOLCHAIN_PREFIX := riscv64-unknown-elf-

# These are microcontroller-specific rules for converting the ELF output
# of the linker into a binary image that can be loaded directly.
CXX             := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)g++'
CC              := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)gcc'
AS              := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)as'
AR              := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)ar' 
LD              := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)ld'
NM              := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)nm'
OBJDUMP         := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)objdump'
OBJCOPY         := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)objcopy'
SIZE            := '$(TARGET_TOOLCHAIN_ROOT)$(TARGET_TOOLCHAIN_PREFIX)size'

RM = rm -f
ARFLAGS := -csr
SRCS := \
tensorflow/lite/micro/simple_memory_allocator.cc\
	tensorflow/lite/micro/micro_error_reporter.cc\
	tensorflow/lite/micro/all_ops_resolver.cc\
	tensorflow/lite/micro/memory_helpers.cc\
	tensorflow/lite/micro/micro_time.cc\
	tensorflow/lite/micro/recording_simple_memory_allocator.cc\
	tensorflow/lite/micro/micro_string.cc\
	tensorflow/lite/micro/micro_profiler.cc\
	tensorflow/lite/micro/micro_utils.cc\
	tensorflow/lite/micro/debug_log.cc\
	tensorflow/lite/micro/micro_allocator.cc\
	tensorflow/lite/micro/test_helpers.cc\
	tensorflow/lite/micro/micro_interpreter.cc\
	tensorflow/lite/micro/recording_micro_allocator.cc\
	tensorflow/lite/micro/benchmarks/keyword_scrambled_model_data.cc\
	tensorflow/lite/micro/memory_planner/linear_memory_planner.cc\
	tensorflow/lite/micro/memory_planner/greedy_memory_planner.cc\
	tensorflow/lite/micro/testing/test_conv_model.cc\
	tensorflow/lite/c/common.c\
	tensorflow/lite/core/api/error_reporter.cc\
	tensorflow/lite/core/api/flatbuffer_conversions.cc\
	tensorflow/lite/core/api/op_resolver.cc\
	tensorflow/lite/core/api/tensor_utils.cc\
	tensorflow/lite/kernels/internal/quantization_util.cc\
	tensorflow/lite/kernels/kernel_util.cc\
	tensorflow/lite/schema/schema_utils.cc\
	tensorflow/lite/micro/kernels/dequantize.cc\
	tensorflow/lite/micro/kernels/ethosu.cc\
	tensorflow/lite/micro/kernels/shape.cc\
	tensorflow/lite/micro/kernels/l2norm.cc\
	tensorflow/lite/micro/kernels/resize_nearest_neighbor.cc\
	tensorflow/lite/micro/kernels/tanh.cc\
	tensorflow/lite/micro/kernels/activations.cc\
	tensorflow/lite/micro/kernels/logistic.cc\
	tensorflow/lite/micro/kernels/arg_min_max.cc\
	tensorflow/lite/micro/kernels/softmax.cc\
	tensorflow/lite/micro/kernels/pad.cc\
	tensorflow/lite/micro/kernels/reduce.cc\
	tensorflow/lite/micro/kernels/unpack.cc\
	tensorflow/lite/micro/kernels/fully_connected.cc\
	tensorflow/lite/micro/kernels/add.cc\
	tensorflow/lite/micro/kernels/ceil.cc\
	tensorflow/lite/micro/kernels/pooling.cc\
	tensorflow/lite/micro/kernels/kernel_runner.cc\
	tensorflow/lite/micro/kernels/split_v.cc\
	tensorflow/lite/micro/kernels/circular_buffer.cc\
	tensorflow/lite/micro/kernels/round.cc\
	tensorflow/lite/micro/kernels/pack.cc\
	tensorflow/lite/micro/kernels/floor.cc\
	tensorflow/lite/micro/kernels/svdf.cc\
	tensorflow/lite/micro/kernels/hard_swish.cc\
	tensorflow/lite/micro/kernels/concatenation.cc\
	tensorflow/lite/micro/kernels/mul.cc\
	tensorflow/lite/micro/kernels/sub.cc\
	tensorflow/lite/micro/kernels/conv.cc\
	tensorflow/lite/micro/kernels/quantize.cc\
	tensorflow/lite/micro/kernels/elementwise.cc\
	tensorflow/lite/micro/kernels/maximum_minimum.cc\
	tensorflow/lite/micro/kernels/reshape.cc\
	tensorflow/lite/micro/kernels/strided_slice.cc\
	tensorflow/lite/micro/kernels/neg.cc\
	tensorflow/lite/micro/kernels/kernel_util.cc\
	tensorflow/lite/micro/kernels/logical.cc\
	tensorflow/lite/micro/kernels/comparisons.cc\
	tensorflow/lite/micro/kernels/depthwise_conv.cc\
	tensorflow/lite/micro/kernels/split.cc\
	tensorflow/lite/micro/kernels/prelu.cc\
        perf.cc

OBJS := \
$(patsubst %.cc,%.o,$(patsubst %.c,%.o,$(SRCS)))

LIBRARY_OBJS := $(filter-out tensorflow/lite/micro/examples/%, $(OBJS))

C_SHARED_FLAGS = \
	-march=rv32im \
	-mabi=ilp32 \
	-fno-unwind-tables \
	-ffunction-sections \
	-fdata-sections \
	-DTF_LITE_STATIC_MEMORY \
	-DTF_LITE_DISABLE_X86_NEON \
	-g \
	-O3 \
	-I. \
	-I./third_party/gemmlowp \
	-I./third_party/flatbuffers/include \
	-I./third_party/ruy \
	-I./third_party/kissfft

ifndef DEBUG
C_SHARED_FLAGS += -DNDEBUG
endif


CXXFLAGS += \
	-std=c++11 \
	-fno-rtti \
	-fno-exceptions \
	-fno-threadsafe-statics \
	-fmessage-length=0 \
	-Werror \
	-Wsign-compare \
	-Wdouble-promotion \
	-Wshadow \
	-Wunused-variable \
	-Wmissing-field-initializers \
	-Wunused-function \
	-Wswitch \
	-Wvla \
	-Wall \
	-Wextra \
	-Wstrict-aliasing \
	-Wno-unused-parameter \
	$(C_SHARED_FLAGS)

CCFLAGS += \
	-std=c11 \
	-fno-unwind-tables \
	$(C_SHARED_FLAGS)

LDFLAGS += -march=rv32im -mabi=ilp32 -Wl,--fatal-warnings -Wl,--gc-sections -lm -lprofiler


# library to be generated
MICROLITE_LIB = libtensorflow-microlite.a

%.o: %.cc
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

%.o: %.c
	$(CC) $(CCFLAGS) $(INCLUDES) -c $< -o $@

person_detection_test_int8 : $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $(OBJS) $(LDFLAGS)


# Creates a tensorflow-litemicro.a which excludes any example code.
$(MICROLITE_LIB): tensorflow/lite/schema/schema_generated.h $(LIBRARY_OBJS)
	@mkdir -p $(dir $@)
	$(AR) $(ARFLAGS) $(MICROLITE_LIB) $(LIBRARY_OBJS)

all: person_detection_test_int8

lib: $(MICROLITE_LIB)

clean:
	-$(RM) $(OBJS)
	-$(RM) person_detection_test_int8
	-$(RM) ${MICROLITE_LIB}
