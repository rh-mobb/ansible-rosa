## Ansible ROSA Modules

### rosa_auth

```
module: rosa_auth

short_description: authenticate with rosa

version_added: "1.0.0"

description: This module assists you with authenticating with ROSA

options:
    token:
        description: The token provided by https://cloud.redhat.com/openshift/token/rosa
        required: true
        type: str
    state:
        description: the action to take
        required: false
        type: str
        choices: ['login','logout']
        default: login

author:
    - Paul Czarkowski (@paulczar)
```

### rosa_init

```
module: rosa_init

short_description: Applies templates to support Red Hat OpenShift Service on AWS.

version_added: "1.0.0"

description: Applies templates to support Red Hat OpenShift Service on AWS.

options:
    token:
        description: The token provided by https://cloud.redhat.com/openshift/token/rosa
        required: false
        type: str
    state:
        description: the action to take
        required: false
        type: str
        choices: ['present','absent']
        default: present

author:
    - Paul Czarkowski (@paulczar)
```

### rosa_cluster

```
module: rosa_cluster

short_description: Create Rosa Cluster

version_added: "1.0.0"

description: Creates ROSA (RedHat Openshift on AWS) Cluster

options:
    name:
        description: Name of the cluster. This will be used when generating a sub-domain for your cluster on openshiftapps.com.
        required: true
        type: str
    multi-az:
        description: Deploy to multiple data centers.
        required: false
        type: bool
    region:
        description: Use a specific AWS region, overriding the AWS_REGION environment variable.
        required: false
        type: str
    version:
        description:  Version of OpenShift that will be used to install the cluster, for example "4.3.10"
        required: false
        type: str
    channel_group:
        description: Channel group is the name of the group where this image belongs, for example "stable" or "fast". (default "stable")
        required: false
        type: str
    compute_machine_type:
        description: Instance type for the compute nodes. Determines the amount of memory and vCPU allocated to each compute node.
        required: false
        type: str
    compute_nodes:
        description: Number of worker nodes to provision per zone. Single zone clusters need at least 2 nodes, multizone clusters need at least 3 nodes. (default 2)
        required: false
        type: int
    enable_autoscaling:
        description: region
        required: false
        type: bool
    min_replicas:
        description: Minimum number of compute nodes. (default 2)
        required: false
        type: int
    max_replicas:
        description: Maximum number of compute nodes. (default 2)
        required: false
        type: int
    machine_cidr:
        description: Block of IP addresses used by OpenShift while installing the cluster, for example "10.0.0.0/16".
        required: false
        type: str
    service_cidr:
        description: Block of IP addresses for services, for example "172.30.0.0/16".
        required: false
        type: str
    pod_cidr:
        description: Block of IP addresses from which Pod IP addresses are allocated, for example "10.128.0.0/14".
        required: false
        type: str
    host_prefix:
        description: Subnet prefix length to assign to each individual node. For example, if host prefix is set to "23", then each node is assigned a /23 subnet out of the given CIDR.
        required: false
        type: int
    private:
        description: Restrict master API endpoint and application routes to direct, private connectivity.
        required: false
        type: bool
    disable_scp_checks:
        description: Indicates if cloud permission checks are disabled when attempting installation of the cluster.
        required: false
        type: bool
    subnet_ids:
        description: The Subnet IDs to use when installing the cluster. SubnetIDs should come in pairs; two per availability zone, one private and one public. Subnets are comma separated, for example: --subnet-ids=subnet-1,subnet-2.Leave empty for installer provisioned subnet IDs.
        required: false
        type: str
    state:
        description: the action to take
        required: false
        type: str
        choices: ['present','absent', 'dry-run']
        default: present

author:
    - Paul Czarkowski (@paulczar)
```