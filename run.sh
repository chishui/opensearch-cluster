#!/bin/bash
VERSION=$1
export OPENSEARCH_INITIAL_ADMIN_PASSWORD=$2
FOLDER_NAME="opensearch-${VERSION}"
FILE_NAME="opensearch-${VERSION}-linux-x64.tar.gz"
DOWNLOAD_URL="https://ci.opensearch.org/ci/dbc/distribution-build-opensearch/${VERSION}/latest/linux/x64/tar/dist/opensearch/opensearch-${VERSION}-linux-x64.tar.gz"

sudo apt update -y > /dev/null
wget ${DOWNLOAD_URL} > /dev/null
tar -xzf ${FILE_NAME}
sudo rm ${FILE_NAME}
# 
sudo swapoff -a
echo 'vm.max_map_count=262144' | sudo tee /etc/sysctl.conf
sudo sysctl -p
ls
#
cd /home/ubuntu/${FOLDER_NAME}

nohup sh opensearch-tar-install.sh > nohup.log 2>&1
sleep 10
pgrep -f "opensearch" | xargs kill -9