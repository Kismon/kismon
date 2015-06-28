PYTHON=`which python3`
DESTDIR=/

all:
	@echo "make install  - Install on local system"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean    - Cleanup files"

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

builddeb:
	dpkg-buildpackage -rfakeroot -b

clean:
	$(PYTHON) setup.py clean
	$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/ MANIFEST debian/compat debian/pycompat
	find . -name '*.pyc' -delete
