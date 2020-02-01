"""Setup script for autotrello package."""

import setup_boilerplate


class Package(setup_boilerplate.Package):
    """Package metadata."""

    name = 'autotrello'
    description = 'Automation of workflows and high-level access to Trello.'
    url = 'https://github.com/mbdevpl/autotrello'
    classifiers = [
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities']
    keywords = ['automation', 'trello']


if __name__ == '__main__':
    Package.setup()
