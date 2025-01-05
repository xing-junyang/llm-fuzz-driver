tar -zxvf libpng-1.6.29.tar.gz
cd libpng-1.6.29
./autogen.sh
./configure --disable-shared
make
echo "libpng prebuild done"