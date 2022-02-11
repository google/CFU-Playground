# Verilated -*- CMake -*-
# DESCRIPTION: Verilator output: CMake include script with class lists
#
# This CMake script lists generated Verilated files, for including in higher level CMake scripts.
# This file is meant to be consumed by the verilate() function,
# which becomes available after executing `find_package(verilator).

### Constants...
set(PERL "perl" CACHE FILEPATH "Perl executable (from $PERL)")
set(VERILATOR_ROOT "/usr/share/verilator" CACHE PATH "Path to Verilator kit (from $VERILATOR_ROOT)")

### Compiler flags...
# User CFLAGS (from -CFLAGS on Verilator command line)
set(Vcfu_USER_CFLAGS )
# User LDLIBS (from -LDFLAGS on Verilator command line)
set(Vcfu_USER_LDLIBS )

### Switches...
# SystemC output mode?  0/1 (from --sc)
set(Vcfu_SC 0)
# Coverage output mode?  0/1 (from --coverage)
set(Vcfu_COVERAGE 0)
# Threaded output mode?  0/1/N threads (from --threads)
set(Vcfu_THREADS 0)
# VCD Tracing output mode?  0/1 (from --trace)
set(Vcfu_TRACE_VCD 0)
# FST Tracing output mode? 0/1 (from --fst-trace)
set(Vcfu_TRACE_FST 0)

### Sources...
# Global classes, need linked once per executable
set(Vcfu_GLOBAL "${VERILATOR_ROOT}/include/verilated.cpp")
# Generated module classes, non-fast-path, compile with low/medium optimization
set(Vcfu_CLASSES_SLOW )
# Generated module classes, fast-path, compile with highest optimization
set(Vcfu_CLASSES_FAST "/home/shivaubuntu/CFU-playground/CFU-Playground/proj/proj_custom/build/renode/CMakeFiles/libVtop.dir/Vcfu.dir/Vcfu.cpp")
# Generated support classes, non-fast-path, compile with low/medium optimization
set(Vcfu_SUPPORT_SLOW "/home/shivaubuntu/CFU-playground/CFU-Playground/proj/proj_custom/build/renode/CMakeFiles/libVtop.dir/Vcfu.dir/Vcfu__Syms.cpp")
# Generated support classes, fast-path, compile with highest optimization
set(Vcfu_SUPPORT_FAST )
# All dependencies
set(Vcfu_DEPS "/home/shivaubuntu/CFU-playground/CFU-Playground/proj/proj_custom/cfu.v" "/usr/bin/verilator_bin")
# User .cpp files (from .cpp's on Verilator command line)
set(Vcfu_USER_CLASSES )
