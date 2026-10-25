#!/usr/bin/env bash
# Mirror this repo (without .git and build artifacts) into the OrbStack Linux
# machine, because Yocto must build on a case-sensitive native Linux filesystem,
# not on a macOS volume.
set -euo pipefail

VM="${VM:-yocto}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DST="${DST:-/home/$USER/rpi5-yocto-ros2}"

orb -m "$VM" rsync -a --delete \
    --exclude='.git' --exclude='.DS_Store' \
    --exclude='/build' --exclude='/downloads' --exclude='/sstate-cache' \
    "$SRC/" "$DST/"
echo "synced $SRC -> $VM:$DST"
