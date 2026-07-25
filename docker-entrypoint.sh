#!/bin/sh
set -eu

chown -R claimlens:claimlens /data
exec su -s /bin/sh -c 'exec "$0" "$@"' -- claimlens "$@"
