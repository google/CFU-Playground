cmake_minimum_required(VERSION 3.8)

# Name of the project
project(cfu)

# C/C++ source files to be compiled
set(CSOURCES sim_main.cpp)

# Additional verilating arguments
if(TRACE_DEPTH_VAL)
    set(TRACE_DEPTH --trace-depth ${TRACE_DEPTH_VAL})
endif()
set(VERI_LIB_ARGS ${ENABLE_TRACE} ${TRACE_DEPTH} -Wno-WIDTH -Wno-CASEINCOMPLETE -Wno-CASEOVERLAP)

# Used by 'sim_main.cpp'.
if(ENABLE_TRACE AND TRACE_FILEPATH)
  add_definitions(-DTRACE_FILEPATH="${TRACE_FILEPATH}")
endif()

find_package(verilator)

file(GLOB_RECURSE RENODE_SOURCES ${VIL_DIR}/cfu.cpp ${VIL_DIR}/renode_cfu.cpp)

add_library(libVtop SHARED ${CSOURCES} ${RENODE_SOURCES})
target_include_directories(libVtop PRIVATE ${VIL_DIR})
target_compile_options(libVtop PRIVATE ${FINAL_LIB_COMP_ARGS})
target_link_libraries(libVtop PRIVATE ${FINAL_LIB_LINK_ARGS})
set_target_properties(libVtop PROPERTIES OUTPUT_NAME Vtop)

verilate(libVtop SOURCES ${VTOP} INCLUDE_DIRS ${INCLUDE_DIR} VERILATOR_ARGS ${VERI_LIB_ARGS})
