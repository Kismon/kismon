#!/usr/bin/env python3

from distutils.core import setup

setup(name='kismon',
	version='0.7',
	description='PyGTK based kismet client',
	author='Patrick Salecker',
	author_email='mail@salecker.org',
	url='https://www.salecker.org/software/kismon.html',
	license='BSD',
	packages=['kismon', 'kismon.windows'],
	scripts=['bin/kismon'],
	platforms='UNIX',
	data_files = [('/usr/share/applications', ['files/kismon.desktop']),
		],
)
