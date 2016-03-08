#!/usr/bin/env python3

from distutils.core import setup
from kismon.utils import get_version

setup(name='kismon',
	version=get_version(),
	description='PyGTK based kismet client',
	author='Patrick Salecker',
	author_email='mail@salecker.org',
	url='https://www.salecker.org/software/kismon.html',
	license='BSD',
	packages=['kismon', 'kismon.widgets', 'kismon.windows'],
	scripts=['bin/kismon'],
	platforms='UNIX',
	data_files = [('/usr/share/applications', ['files/kismon.desktop']),
		],
)
