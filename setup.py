from setuptools import (setup, find_packages)

__VERSION__ = "0.1.0"
__RELEASE_DATE__ = "20-Jul-2024"
__AUTHOR__ = "Gustau Castells(karasu)"
__AUTHOR_EMAIL__ = "inabox@ies-sabadell.cat"


def get_requirements():
    """ Get dependencies """
    return open('requirements.txt', 'rt', encoding='utf-8').read().splitlines()


setup(
    name='martor',
    version=__VERSION__,
    packages=find_packages(exclude=["*demo"]),
    include_package_data=True,
    zip_safe=False,
    description='Django Markdown Editor',
    url='https://github.com/karasu/inabox',
    download_url=f'https://github.com/karasu/inabox/tarball/v{__VERSION__}',
    keywords=['martor', 'django markdown', 'django markdown editor'],
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    license='GNUGPL-v3',
    author=__AUTHOR__,
    author_email=__AUTHOR_EMAIL__,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    install_requires=get_requirements(),
)
