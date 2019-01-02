#!/usr/bin/env python3

import platform
from setuptools import setup
from kismon.utils import get_version

data_files = []

platform_system = platform.system()
if platform_system == 'Linux' or platform_system.endswith('BSD'):
	data_files.append(('/usr/share/applications', ['files/kismon.desktop']))

setup(name='kismon',
	version=get_version(),
	description='A GUI client for kismet (wireless scanner/sniffer/monitor)',
	author='Patrick Salecker',
	author_email='mail@salecker.org',
	url='https://www.salecker.org/software/kismon.html',
	license='BSD',
	packages=['kismon', 'kismon.widgets', 'kismon.windows'],
	scripts=['bin/kismon'],
	platforms='UNIX',
	data_files = data_files,
)
