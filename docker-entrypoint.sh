#!/bin/sh
set -eu

chown -R claimlens:claimlens /data
exec su -s /bin/sh -c 'exec "$@"' claimlens claimlens "$@"
