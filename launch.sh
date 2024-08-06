#!/bin/bash
INITIAL_PASSWORD=$1
if pgrep -f "opensearch" > /dev/null
then
    echo "Process found. Attempting to kill..."
    # Kill the process
    pgrep -f "opensearch" | xargs kill -9
    echo "Process killed."
    sleep 10
else
    echo "Process not found. Continuing..."
fi
export OPENSEARCH_INITIAL_ADMIN_PASSWORD=$1
nohup sh opensearch-tar-install.sh > nohup.log 2>&1 &
sleep 2
pgrep -f opensearch
