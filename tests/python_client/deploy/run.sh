#!/bin/bash
set -x

# start test standalone reinstall
bash test.sh standalone reinstall
# start test standalone upgrade
bash test.sh standalone upgrade
# start test cluster reinstall
bash test.sh cluster reinstall
# start test cluster upgrade
bash test.sh cluster upgrade
