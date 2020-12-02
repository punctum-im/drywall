#!/bin/sh
coverage erase
set -e
coverage run -a --source=drywall -m pytest;
sed -i "s/backend\": \"dummy\"/backend\": \"sqlite\"/g" "config.json"
set +e; [ -e drywall.db ] && mv drywall.db drywall_old.db; set -e
coverage run -a --source=drywall -m pytest tests/test_db.py; coverage xml
rm drywall.db
set +e; [ -e drywall_old.db ] && mv drywall_old.db drywall.db
exit 0
