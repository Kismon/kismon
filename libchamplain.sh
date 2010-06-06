mkdir champlain
cd champlain

# install general dependenies
sudo apt-get install git-core autoconf libtool gtk-doc-tools libsqlite3-dev libclutter-1.0-dev libsoup-gnome2.4-dev libclutter-gtk-0.10-dev
# install python dependenies
sudo apt-get install python-dev python-gobject-dev python-gtk2-dev python-clutter-dev python-clutter-gtk-dev python-cairo-dev

# download and install libmemphis
wget https://trac.openstreetmap.ch/trac/memphis/downloads/3 --no-check-certificate -O memphis-0.2.1.tar.gz 
tar -xf memphis-0.2.1.tar.gz
cd memphis-0.2.1
./configure
make
sudo make install
cd ..

# download and install memphis python bindings
git clone git://gitorious.org/pymemphis/mainline.git pymemphis
cd pymemphis
./autogen.sh
make
sudo make install
cd ..

# download and install libchamplain
#git clone git://git.gnome.org/libchamplain
wget http://download.gnome.org/sources/libchamplain/0.6/libchamplain-0.6.0.tar.gz
tar -xf libchamplain-0.6.0.tar.gz
cd libchamplain-0.6.0
#./autogen.sh
./configure --enable-python
make
sudo make install
sudo ldconfig

# test python bindings
python bindings/python/demos/launcher-gtk.py
