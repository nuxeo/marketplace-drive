r"""Fetch the installer packages for Nuxeo Drive from the related Jenkins jobs

The fetch-installers command allows to fetch both .msi and .dmg binary packages
from Jenkins using the given URL parameters and put them in the 'drive'
template directory of the marketplace package.

Get the help on running this with::

    python fetch_installer_packages.py --help

"""

import os
import sys
import urllib2
import argparse
import re
import shutil
import subprocess


LINKS_PATTERN = r'\bhref="([^"]+)"'

MSI_PATTERN = r"nuxeo-drive-.*\.msi"
DMG_PATTERN = r"Nuxeo%20Drive\.dmg"

TEMPLATE_FOLDER = os.path.join("target", "marketplace",
    "install", "templates", "drive", "client")


def pflush(message):
    """This is required to have messages in the right order in Jenkins"""
    print message
    sys.stdout.flush()


def parse_args(args=None):
    main_parser = argparse.ArgumentParser(
        description="Fetch Nuxeo Drive installer packages")
    subparsers = main_parser.add_subparsers(title="Commands")

    # Fetch installer packages from related Jenkins jobs
    parser = subparsers.add_parser(
        'fetch-installers', help="Fetch installer packages from Jenkins pages")
    parser.set_defaults(command='fetch-installers')
    parser.add_argument('--msi-url')
    parser.add_argument('--dmg-url')
    parser.add_argument('--base-folder')

    return main_parser.parse_args(args)


def download(url, filename):
    if not os.path.exists(filename):
        pflush("Downloading %s to %s" % (url, filename))
        headers = {'User-Agent': 'nxdrive test script'}
        req = urllib2.Request(url, None, headers)
        reader = urllib2.urlopen(req)
        with open(filename, 'wb') as f:
            while True:
                b = reader.read(1000 ** 2)
                if b == '':
                    break
                f.write(b)


def find_package_url(archive_page_url, pattern):
    pflush("Finding latest package at: " + archive_page_url)
    index_html = urllib2.urlopen(archive_page_url).read()
    candidates = []
    archive_pattern = re.compile(pattern)
    for link in re.compile(LINKS_PATTERN).finditer(index_html):
        link_url = link.group(1)
        if "/" in link_url:
            link_filename = link_url.rsplit("/", 1)[1]
        else:
            link_filename = link_url
        if archive_pattern.match(link_filename):
            candidates.append(link_url)

    if not candidates:
        raise ValueError("Could not find packages with pattern %r on %s"
                         % (pattern, archive_page_url))
    candidates.sort()
    archive = candidates[0]
    if archive.startswith("http"):
        archive_url = archive
    else:
        if not archive_page_url.endswith('/'):
            archive_page_url += '/'
        archive_url = archive_page_url + archive
    return archive_url, archive_url.rsplit('/', 1)[1]


def download_package(url, pattern, target_folder):
    if pattern is None:
        filename = url.rsplit("/", 1)[1]
    else:
        url, filename = find_package_url(url, pattern)
    filepath = os.path.join(target_folder, urllib2.unquote(filename))
    download(url, filepath)


if __name__ == "__main__":
    options = parse_args()

    if options.command == 'fetch-installers':
        target_folder = os.path.join(options.base_folder, TEMPLATE_FOLDER)
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)
        os.makedirs(target_folder)
        if options.msi_url is not None:
            download_package(options.msi_url, MSI_PATTERN, target_folder)
        if options.dmg_url is not None:
            download_package(options.dmg_url, DMG_PATTERN, target_folder)
