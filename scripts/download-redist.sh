#!/bin/bash
set -e
SCRIPT=$(realpath "$0")

VERSION=$1
OS=$2
TARGET_PATH=$3
CHECKSUMS=$(dirname "$SCRIPT")/checksums.txt

case $OS in
  Linux)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/
    MQC_REDIST_ARCHIVE=${VERSION}-IBM-MQC-Redist-LinuxX64.tar.gz
    ;;
  Windows)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist/
    MQC_REDIST_ARCHIVE=${VERSION}-IBM-MQC-Redist-Win64.zip
    ;;
  macOS)
    BASE_URL=https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/mactoolkit/
    MQC_REDIST_ARCHIVE=${VERSION}-IBM-MQ-DevToolkit-MacOS.pkg
    ;;
  *)
    >&2 echo "Unsupported OS $OS"
    exit 1
    ;;
esac

grep $MQC_REDIST_ARCHIVE $CHECKSUMS > /dev/null || (>&2 echo "Unknown archive $MQC_REDIST_ARCHIVE"; exit 1)

mkdir -p $TARGET_PATH
cd $TARGET_PATH

grep $MQC_REDIST_ARCHIVE $CHECKSUMS | sha256sum --check --status 2>&1 > /dev/null || \
  curl -o $MQC_REDIST_ARCHIVE --retry 10 --retry-connrefused --location --silent --show-error --fail ${BASE_URL}${MQC_REDIST_ARCHIVE}

grep $MQC_REDIST_ARCHIVE $CHECKSUMS | sha256sum --check --status

echo $TARGET_PATH/$MQC_REDIST_ARCHIVE
