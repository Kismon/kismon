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
	rm -rf build/ MANIFEST .pybuild/
	find . -name '*.pyc' -delete

test:
	python3 -m unittest discover -v

test-coverage:
	python3-coverage run --source=kismon/ -m unittest discover
	python3-coverage report
	python3-coverage html
