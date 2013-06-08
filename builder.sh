#!/bin/bash

p4 edit linux32/...
p4 edit linux64/...

rm -rf ./linux32
rm -rf ./linux64

cmake -DCMAKE_C_FLAGS=-m32 -DCMAKE_CXX_FLAGS=-m32 -DCMAKE_EXE_LINKER_FLAGS=-m32 -DCMAKE_SYSTEM_LIBRARY_PATH=/user/lib32 -DENABLE_GUI=FALSE -DCMAKE_CXX_COMPILER=g++-4.6 -H. -Blinux32
make -C linux32

cmake -DCMAKE_CXX_COMPILER=g++-4.4 -H. -Blinux64
make -C linux64
