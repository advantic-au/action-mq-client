#!/bin/bash
set -e
SCRIPT=$(realpath "$0")

VERSION=$1
OS=$2

ALIASES=$(dirname "${SCRIPT}")/../aliases.json

VERSION_ALIAS=$(jq -r ."\"${VERSION}\".\"${OS}\"" < "${ALIASES}")
case $VERSION_ALIAS in
  null)
    echo "${VERSION}"
    ;;
  *)
    echo "${VERSION_ALIAS}"
    ;;
esac
