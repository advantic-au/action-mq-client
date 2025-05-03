#!/bin/bash
set -e
SCRIPT=$(realpath "$0")

VERSION=$1
OS=$2
TARGET_PATH=$3
CHECKSUMS=$(dirname "${SCRIPT}")/../checksums.txt

unameOut="$(uname -s)"
case "${unameOut}" in
    Darwin*)    SHA256="shasum -a 256";;
    *)          SHA256="sha256sum";;
esac

case $OS in
  LinuxX64)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/
    MQ_CLIENT_ARCHIVE=${VERSION}-IBM-MQC-Redist-LinuxX64.tar.gz
    ;;
  LinuxARM64)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqadv/
    MQ_CLIENT_ARCHIVE=${VERSION}-IBM-MQ-Advanced-for-Developers-Non-Install-LinuxARM64.tar.gz
    ;;
  LinuxPPC64LE)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqadv/
    MQ_CLIENT_ARCHIVE=${VERSION}-IBM-MQ-Advanced-for-Developers-Non-Install-LinuxPPC64LE.tar.gz
    ;;
  LinuxS390X)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqadv/
    MQ_CLIENT_ARCHIVE=${VERSION}-IBM-MQ-Advanced-for-Developers-Non-Install-LinuxS390X.tar.gz
    ;;
  WindowsX64)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/
    MQ_CLIENT_ARCHIVE=${VERSION}-IBM-MQC-Redist-Win64.zip
    ;;
  macOS*)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/mactoolkit/
    MQ_CLIENT_ARCHIVE=${VERSION}-IBM-MQ-DevToolkit-MacOS.pkg
    ;;
  *)
    >&2 echo "Unsupported OS ${OS}"
    exit 1
    ;;
esac

grep "${MQ_CLIENT_ARCHIVE}" "${CHECKSUMS}" > /dev/null || (>&2 echo "Unknown archive ${MQ_CLIENT_ARCHIVE}"; exit 1)

mkdir -p "${TARGET_PATH}"
cd "${TARGET_PATH}"

grep "${MQ_CLIENT_ARCHIVE}" "${CHECKSUMS}" | ${SHA256} --check --status > /dev/null 2>&1 || (
  curl -o "${MQ_CLIENT_ARCHIVE}" --retry 5 --retry-connrefused --location --silent --fail "${BASE_URL}${MQ_CLIENT_ARCHIVE}"
)
grep "${MQ_CLIENT_ARCHIVE}" "${CHECKSUMS}" | ${SHA256} --check --status || (>&2 echo "File checksum validation failure"; exit 1)

echo "${TARGET_PATH}/${MQ_CLIENT_ARCHIVE}"
