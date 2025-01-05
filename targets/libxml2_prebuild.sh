tar -zxvf libxml2-2.13.4.tar.gz
cd libxml2-2.13.4
./autogen.sh
./configure --disable-shared
make
echo 'libxml2 build done'