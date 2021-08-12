#!/bin/bash
set -e -x

sudo dnf install -y wget curl python36 python36-devel net-tools gcc libffi-devel openssl-devel jq

# mitmproxy

cd /tmp
wget -O /tmp/mitmproxy.tar.gz https://snapshots.mitmproxy.org/7.0.0/mitmproxy-7.0.0-linux.tar.gz
tar xzvf /tmp/mitmproxy.tar.gz
sudo install /tmp/mitmproxy /usr/local/bin/mitmproxy

wget https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-client-linux.tar.gz

mkdir openshift
tar -zxvf openshift-client-linux.tar.gz -C openshift
sudo install openshift/oc /usr/local/bin/oc
sudo install openshift/kubectl /usr/local/bin/kubectl
