#!/bin/bash -x

set -e
cd mwlib
python setup.py build_ext --inplace build 
find build -type f -name '_*.so' | xargs -iFILE cp FILE mwlib/ 