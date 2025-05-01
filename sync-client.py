import requests
import hashlib
import re
import sys
from bs4 import BeautifulSoup, SoupStrainer
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urljoin, unquote, urlparse
from pathlib import PurePosixPath

checksum_filename = sys.argv[1]

checksum_file = open(checksum_filename, "r")
files = dict([tuple(reversed(line.rstrip().split())) for line in checksum_file.readlines()])
checksum_file.close()

linux_x64_re = re.compile(".*?IBM-MQC-Redist-LinuxX64\\.tar\\.gz")
linux_arm64_re = re.compile(".*?IBM-MQ-Advanced-for-Developers-Non-Install-LinuxARM64\\.tar\\.gz")
win_re = re.compile(".*?IBM-MQC-Redist-Win64\\.zip")
mac_re = re.compile(".*?IBM-MQ-DevToolkit-MacOS\\.pkg")

def is_client_archive(file):
    return win_re.fullmatch(file) or linux_x64_re.fullmatch(file) or linux_arm64_re.fullmatch(file) or mac_re.fullmatch(file)

def sha256_url(url):
    m = hashlib.sha256()
    s = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    with s.get(url, stream=True, timeout=10) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            m.update(chunk)
    return m.hexdigest()

def new_client_files(url_list, output):
    client_url_list = [];
    for url in url_list:
        response = requests.get(url)
        a_links = BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('a'))
        hrefs = [link["href"] for link in a_links if link.has_attr('href')]
        client_url_list.extend([urljoin(url, archive_file) for archive_file in hrefs if is_client_archive(archive_file) ])

    for client_url in client_url_list:
        file_name = PurePosixPath(unquote(urlparse(client_url).path)).parts[-1]
        sha = files.get(file_name)
        if sha == None:
            print("Downloading file for sha256: " + file_name, flush=True)
            sha = sha256_url(client_url)
        output.write(sha + "  " + file_name + "\n")
        output.flush()

client_url = [
    "https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/?C=M;O=A",
    "https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/mactoolkit/?C=M;O=A",
    "https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqadv/?C=M;O=A"
]

with open(checksum_filename, "w") as checksum_write:
    new_client_files(client_url, checksum_write)
