import requests
import hashlib
import re
import sys
from bs4 import BeautifulSoup, SoupStrainer


checksum_filename = sys.argv[1]

checksum_file = open(checksum_filename, "r")
files = set([line.rstrip().split()[-1] for line in checksum_file.readlines()])
checksum_file.close()

linux_re = re.compile(".*?LinuxX64\\.tar\\.gz")
win_re = re.compile(".*?Win64\\.zip")
mac_re = re.compile(".*?MacOS\\.pkg")

def is_redist(file):
    return win_re.fullmatch(file) or linux_re.fullmatch(file) or mac_re.fullmatch(file)

def sha256_url(url):
    m = hashlib.sha256()
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            m.update(chunk)
    return m.hexdigest()

def new_redist_files(url, output):
    response = requests.get(url)
    a_links = BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('a'))
    hrefs = [link["href"] for link in a_links if link.has_attr('href')]
    redist_files = set([redist_file for redist_file in hrefs if is_redist(redist_file) ])

    new_files = list(redist_files - files)
    new_files.sort()

    for file in new_files:
        print("Downloading file for sha256: " + file)
        output.write(sha256_url(url + file) + "  " + file + "\n")
        output.flush()

with open(checksum_filename, "a") as checksum_write:
    new_redist_files("https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/", checksum_write)
    new_redist_files("https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/mactoolkit/", checksum_write)
