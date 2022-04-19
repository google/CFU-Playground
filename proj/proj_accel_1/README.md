This directory contains rachsug's project work.

Since completion of the project, there have been updates by others in order to work with a new build system. In particular:

(a) moving tflm_overlay to src
(b) updating the old standard cfu_gen.py to the new standard cfu_gen.py.
(c) changes to the Makefile to use the new build system
(d) changed name of binary used by renode
(e) removing basic_cfu directory, as it was unused

Small further changes were required when the cfu_opX() macros was refactored to have 3 parameters rather than 2.

There was one bug fix:

 *  Commit b2dac48dd09e0707d2aafd8b91f2e3beca2be13d:
    The specialized version of the routine unrolls the inner loop by a factor of 8,
    and only works correctly when the number of iterations is a multiple of 8.
    The check for meeting the specialization criteria failed to check for
    this requirement.

There have been no significant updates to other parts of the directory.
