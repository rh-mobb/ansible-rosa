# ansible-rosa

This project contains a set of modules for working with ROSA as well as some example playbooks.

Will create/delete ROSA clusters, by default a single cluster called `demo`, but if you know how to work ansible inventories, it can do multiple clusters. By default the cluster will be
a public cluster on a BYO VPC network with STS enabled.

## ROSA Ansible Modules

> See [here](docs/modules.md) for detailed documentation

```yaml
- name: authenticate rosa using token
  rosa_auth:
    token: "{{ rosa_token }}"

- name: initialize rosa
  rosa_init:
    state: present

- name: create cluster
  rosa_cluster:
    name: "my-rosa-cluster"
    compute_nodes: 4
    multi_az: no
    wait: true
```

## Examples using ROSA Ansible Modules

## Prerequisites

1. Create a [Red Hat](https://cloud.redhat.com) account, if you do not already have one. Then, check your email for a verification link. You will need these credentials to install ROSA.

1. Download and install the [AWS cli](https://aws.amazon.com/cli/)

1. Download and install the [ROSA cli 1.0.9+](https://github.com/openshift/rosa/releases/tag/v1.0.9)

1. Enable the ROSA service in AWS.

    1. Sign in to your AWS account.
    1. Go to the [ROSA service](https://console.aws.amazon.com/rosa/) and select **Enable**.

## Log in to AWS or ROSA

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

## Local with ansible in a virtualenv

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

## Local using Docker

> not tested recently

1. Build the docker image

    ```bash
    make image
    ```

2. Create the cluster (do *one* of the following)

    * If you've already logged in locally:

    ```bash
    docker run -ti \
      -v $HOME/.ocm.json:/ansible/.ocm.json:ro \
      -v $HOME/.aws:/ansible/.aws:ro paulczar/ansible-rosa \
      ansible-playbook create-sts-cluster.yaml
    ```

    * If you want to let ansible log you in:

    ```bash
    docker run -ti -e AWS_ACCESS_KEY_ID="" \
       -e AWS_SECRET_ACCESS_KEY="" -e ROSA_TOKEN="" \
       paulczar/ansible-rosa \
       ansible-playbook create-sts-cluster.yaml
    ```

3. Delete the cluster

    Do one of the above but change `create-sts-cluster.yaml` to `delete-sts-cluster.yaml`.


## ToDos

### Add custom domain support

* https://access.redhat.com/articles/5599621
* https://github.com/openshift/custom-domains-operator/blob/master/TESTING.md