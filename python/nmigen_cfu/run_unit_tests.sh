#!/bin/bash
pushd $(dirname ${BASH_SOURCE[0]})
../../scripts/pyrun -m unittest $*
popd