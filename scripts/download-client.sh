#!/bin/bash
set -e
SCRIPT=$(realpath "$0")

VERSION=$1
OS=$2
TARGET_PATH=$3
CHECKSUMS=$(dirname "${SCRIPT}")/../checksums.txt

case $OS$ARCH in
  LinuxX64)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/
    MQC_REDIST_ARCHIVE=${VERSION}-IBM-MQC-Redist-LinuxX64.tar.gz
    SHA256=sha256sum
    ;;
  LinuxARM64)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqadv/
    MQC_REDIST_ARCHIVE=${VERSION}-IBM-MQ-Advanced-for-Developers-Non-Install-LinuxARM64.tar.gz
    SHA256=sha256sum
    ;;
  Windows*)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/
    MQC_REDIST_ARCHIVE=${VERSION}-IBM-MQC-Redist-Win64.zip
    SHA256=sha256sum
    ;;
  macOS*)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/mactoolkit/
    MQC_REDIST_ARCHIVE=${VERSION}-IBM-MQ-DevToolkit-MacOS.pkg
    SHA256="shasum -a 256"
    ;;
  *)
    >&2 echo "Unsupported OS ${OS}${ARCH}"
    exit 1
    ;;
esac

grep "${MQC_REDIST_ARCHIVE}" "${CHECKSUMS}" > /dev/null || (>&2 echo "Unknown archive ${MQC_REDIST_ARCHIVE}"; exit 1)

mkdir -p "${TARGET_PATH}"
cd "${TARGET_PATH}"

grep "${MQC_REDIST_ARCHIVE}" "${CHECKSUMS}" | ${SHA256} --check --status > /dev/null 2>&1 || \
  curl -o "${MQC_REDIST_ARCHIVE}" --retry 10 --retry-connrefused --location --silent --show-error --fail "${BASE_URL}${MQC_REDIST_ARCHIVE}"

grep "${MQC_REDIST_ARCHIVE}" "${CHECKSUMS}" | ${SHA256} --check --status || (>&2 echo "File checksum validation failure"; exit 1)

echo "${TARGET_PATH}/${MQC_REDIST_ARCHIVE}"
