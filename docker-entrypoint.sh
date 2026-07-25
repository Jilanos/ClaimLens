#!/bin/sh
set -eu

chown -R claimlens:claimlens /data
exec su -s /bin/sh claimlens -c 'exec "$0" "$@"' "$@"
