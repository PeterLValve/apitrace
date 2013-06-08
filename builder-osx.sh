#/bin/sh

rm -rf osx64
rm -rf osx32

cmake -H. -Bosx64
make -C osx64

cmake \
    -DCMAKE_C_FLAGS=-m32 \
    -DCMAKE_CXX_FLAGS=-m32 \
    -DCMAKE_OSX_ARCHITECTURES=i386 \
    -DCMAKE_EXE_LINKER_FLAGS=-m32 \
    -DCMAKE_SYSTEM_LIBRARY_PATH=/usr/lib32 \
    -DENABLE_GUI=FALSE \
    -H. -Bosx32
make -C osx32