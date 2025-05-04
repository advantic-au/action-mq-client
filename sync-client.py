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
sha_lookup = dict([tuple(reversed(line.rstrip().split())) for line in checksum_file.readlines()])
checksum_file.close()

linux_x64_re = re.compile(".*?IBM-MQC-Redist-LinuxX64\\.tar\\.gz")
linux_mqadv_re = re.compile(".*?IBM-MQ-Advanced-for-Developers-Non-Install-Linux(ARM64|PPC64LE|S390X)\\.tar\\.gz")
win_re = re.compile(".*?IBM-MQC-Redist-Win64\\.zip")
mac_re = re.compile(".*?IBM-MQ-DevToolkit-MacOS\\.pkg")

def is_client_archive(file):
    return win_re.fullmatch(file) or linux_x64_re.fullmatch(file) or linux_mqadv_re.fullmatch(file) or mac_re.fullmatch(file)

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

def client_url_list(ibm_url_list):
    client_url_list = [];
    for url in ibm_url_list:
        response = requests.get(url)
        a_links = BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('a'))
        hrefs = [link["href"] for link in a_links if link.has_attr('href')]
        for archive_file in hrefs:
            if is_client_archive(archive_file):
                full_client_url = urljoin(url, archive_file)
                client_file_name = PurePosixPath(unquote(urlparse(full_client_url).path)).parts[-1]
                client_url_list.append((client_file_name, full_client_url))
    return client_url_list

ibm_url_list = [
    "https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/?C=M;O=A",
    "https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/mactoolkit/?C=M;O=A",
    "https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqadv/?C=M;O=A"
]

client_list = client_url_list(ibm_url_list)

with open(checksum_filename, "w") as checksum_write:
    for (file_name, url) in client_list:
        if sha_lookup.get(file_name) != None:
            checksum_write.write(sha_lookup[file_name] + "  " + file_name + "\n")
            checksum_write.flush()

with open(checksum_filename, "a") as checksum_write:
    for (file_name, client_url) in client_list:
        if sha_lookup.get(file_name) == None:
            print("Downloading file for sha256: " + file_name, flush=True)
            sha = sha256_url(client_url)
            sha_lookup[file_name] = sha
            checksum_write.write(sha + "  " + file_name + "\n")
            checksum_write.flush()

with open(checksum_filename, "w") as checksum_write:
    for (file_name, url) in client_list:
        checksum_write.write(sha_lookup[file_name] + "  " + file_name + "\n")
        checksum_write.flush()
