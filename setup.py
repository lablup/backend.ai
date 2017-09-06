from setuptools import setup
from pathlib import Path


setup(
    name='sorna',
    version='1.0.0',
    description='Sorna Meta-package',
    long_description=Path('README.rst').read_text(),
    url='https://github.com/lablup/sorna',
    author='Lablup Inc.',
    author_email='devops@lablup.com',
    license='LGPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Environment :: No Input/Output (Daemon)',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
    ],

    packages=['sorna'],
    namespace_packages=['sorna'],

    python_requires='>=3.6',
    install_requires=[
        'sorna-common~=1.0.0',
    ],
    extras_require={
        'manager': [
            'sorna-manager~=1.0.0',
        ],
        'agent': [
            'sorna-agent~=1.0.0',
        ],
    },
    data_files=[],
)
