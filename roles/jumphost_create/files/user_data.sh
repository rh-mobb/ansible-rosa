#!/bin/bash
set -e -x

sudo dnf install -y python3 python3-devel python3-pip
sudo pip3 install requests-oauthlib
sudo dnf install -y wget curl net-tools gcc libffi-devel openssl-devel jq bind-utils podman

wget https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/openshift-client-linux.tar.gz

mkdir openshift
tar -zxvf openshift-client-linux.tar.gz -C openshift
sudo install openshift/oc /usr/local/bin/oc
sudo install openshift/kubectl /usr/local/bin/kubectl
