#!/usr/bin/env python

from distutils.core import setup

setup(name='ukai',
      version='0.1',
      description='Location-aware Distributed Storage for Virtual Machines',
      author='Keiichi SHIMA',
      author_email='keiichi@iijlab.net',
      url='http://github.com/keiichishima/ukai/',
      packages=['ukai'],
      requires=['fusepy (>=2.0.2)', 'netifaces (>=0.6)'],
      scripts=['scripts/ukai_create_image.py',
               'scripts/ukai_get_image_info.py',
               'scripts/ukai_add_image.py',
               'scripts/ukai_remove_image.py',
               'scripts/ukai_add_location.py',
               'scripts/ukai_remove_location.py',
               'scripts/ukai_add_hypervisor.py',
               'scripts/ukai_remove_hypervisor.py',
               'scripts/ukai_synchronize.py',
               'scripts/ukai_get_statistics.py',
               'scripts/ukai_get_error_state.py',
               ],
      data_files=[('share/doc/ukai', ['README.md', 'ukai_logo.png'])],
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Filesystems',
        ],
)
