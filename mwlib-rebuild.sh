#!/bin/bash -x

set -e

platform=`python3 -c 'import sys, platform; \
    print("%s%s_%s%s" % (platform.system().lower(),
                          platform.architecture()[0][0:2],
                          sys.version_info.major,
                          sys.version_info.minor))' `


python3 setup.py-mwlib build_ext --inplace build 
mkdir -p binarylibs/$platform/
find build -type f -name '_*.so' | xargs -iFILE cp FILE binarylibs/$platform/