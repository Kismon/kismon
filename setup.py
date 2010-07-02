#!/usr/bin/env python

from distutils.core import setup

setup(name='kismon',
	version='0.1',
	description='PyGTK based kismet client',
	author='Patrick Salecker',
	author_email='mail@salecker.org',
	url='http://gitorious.org/kismon',
	license='BSD',
	packages=['kismon'],
	scripts=['bin/kismon'],
	platforms='UNIX',
	data_files = [('/usr/share/applications', ['files/kismon.desktop']),
		('/usr/share/kismon',
			['files/open.png', 'files/wep.png', 'files/wpa.png', 'files/position.png']),
		],
)
