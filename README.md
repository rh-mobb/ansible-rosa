# ansible-rosa

*******************************************************************
* 							          *
*  This project is provided as-is, and is not an official or      *
*  Supported Red Hat project. We will happily accept issues and   *
*  Pull Requests and provide basic OSS level community support    *
*******************************************************************

This project contains a set of modules for working with ROSA as well as some example playbooks.

Will create/delete ROSA clusters but if you know how to work ansible inventories, it can do multiple clusters. By default the cluster will be a single-az public cluster on a BYO VPC network with STS enabled.  modify the inventory in `environment/default` to enable private-link or modify networks.


## Examples using ROSA Ansible Modules

## Prerequisites

1. Create a [Red Hat](https://cloud.redhat.com) account, if you do not already have one. Then, check your email for a verification link. You will need these credentials to install ROSA.

1. Download and install the [AWS cli](https://aws.amazon.com/cli/)

1. Download and install the [ROSA cli 1.0.9+](https://github.com/openshift/rosa/releases/tag/v1.0.9)

1. Enable the ROSA service in AWS.

    1. Sign in to your AWS account.
    1. Go to the [ROSA service](https://console.aws.amazon.com/rosa/) and select **Enable**.

## Log in to AWS and ROSA

To authenticate to AWS / ROSA you can use the tools directly to auth or set ansible variables and let it do it for you.

### Login First

1. Configure aws cli

    ```bash
    aws configure
    ```

2. Configure rosa

    ```bash
    rosa login
    ```

## Deploy a Cluster with ansible in a virtualenv

### Prepare Ansible

Create python virtualenv:

```bash
make virtualenv
```

### Deploy a cluster

```bash
make create
```

### Delete a cluster

```bash
make delete
```

## Deploy a Cluster with ansible in a docker image

1. Build the docker image

    ```bash
    make image
    ```

2. Create the cluster (do *one* of the following)

    * If you've already logged in locally:

    ```bash
    make docker.create
    ```

    * If you want to let ansible log you in (fill out the variables):

    ```bash
    docker run -ti -e AWS_ACCESS_KEY_ID="" \
       -e AWS_SECRET_ACCESS_KEY="" -e ROSA_TOKEN="" \
       quay.io/pczar/ansible-rosa \
       ansible-playbook create-cluster.yaml
    ```

3. Delete the cluster

    ```bash
    make docker.delete
    ```

    or

    ```bash
    docker run -ti -e AWS_ACCESS_KEY_ID="" \
       -e AWS_SECRET_ACCESS_KEY="" -e ROSA_TOKEN="" \
       quay.io/pczar/ansible-rosa \
       ansible-playbook delete-cluster.yaml
    ```


## ToDos

### Add custom domain support

* https://access.redhat.com/articles/5599621
* https://github.com/openshift/custom-domains-operator/blob/master/TESTING.md
