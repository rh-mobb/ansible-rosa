#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ocm_cluster

short_description: Create Rosa Cluster

version_added: "1.0.0"

description: Creates ROSA (RedHat Openshift on AWS) Cluster via OCM API.

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
    http_proxy:
        description: HTTP proxy to use for OpenShift.
        required: false
        type: str
    https_proxy:
        description: HTTPS proxy to use for OpenShift.
        required: false
        type: str
    additional_trust_bundle_file:
        description: Path to a file containing additional trust bundle for proxy.
        required: false
        type: str
    private-link:
        description: Provides private connectivity between VPCs, AWS services, and your on-premises networks, without exposing your traffic to the public internet.
        required: false
        type: bool
    private:
        description: Restrict master API endpoint and application routes to direct, private connectivity.
        required: false
        type: bool
    disable_scp_checks:
        description: Indicates if cloud permission checks are disabled when attempting installation of the cluster.
        required: false
        type: bool
    disable_workload_monitoring:
        description: disable user workload monitoring for the cluster.
        required: false
        default: false
        type: bool
    subnet_ids:
        description: The Subnet IDs to use when installing the cluster. SubnetIDs should come in pairs; two per availability zone, one private and one public. Subnets are comma separated, for example: --subnet-ids=subnet-1,subnet-2.Leave empty for installer provisioned subnet IDs.
        required: false
        type: str
    sts:
        description: Enable STS auth, a set of roles will be needed.
        required: false
        type: bool
    aws_account_id:
        description: AWS account ID, only required if STS is enabled.
        required: false
        type: str
    wait:
        description: wait for up to an hour until operation is complete
        required: false
        type: bool
    kms_key_arn:
        description: kms key (BYOK)
        required: false
        type: str
    state:
        description: the action to take
        required: false
        type: str
        choices: ['present','absent', 'dry-run', 'describe']
        default: present

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: Create a rosa cluster using all defaults
  ocm_cluster:
    name: my-rosa-cluster
    state: present

- name: delete a rosa cluster
  ocm_cluster:
    name: my-rosa-cluster
    state: absent
'''

RETURN = r'''
cluster:
    description: Cluster object from OCM
    type: dict
changed:
    description: Whether a cluster was created or deleted
    type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ocm_cluster_lib import ocm_cluster_run


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        region=dict(type='str', required=False),
        version=dict(type='str', required=False, default="4.8.2"),
        channel_group=dict(type='str', required=False),
        compute_machine_type=dict(type='str', required=False),
        compute_nodes=dict(type='str', required=False),
        min_replicas=dict(type='str', required=False),
        max_replicas=dict(type='str', required=False),
        machine_cidr=dict(type='str', required=False),
        service_cidr=dict(type='str', required=False),
        pod_cidr=dict(type='str', required=False),
        host_prefix=dict(type='int', required=False),
        http_proxy=dict(type='str', required=False),
        https_proxy=dict(type='str', required=False),
        no_proxy=dict(type='str', required=False),
        additional_trust_bundle_file=dict(type='str', required=False),
        subnet_ids=dict(type='str', required=False),
        multi_az=dict(type='bool', required=False),
        private=dict(type='bool', required=False),
        private_link=dict(type='bool', required=False),
        sts=dict(type='bool', required=False),
        aws_account_id=dict(type='str', required=False),
        disable_scp_checks=dict(type='bool', required=False),
        disable_workload_monitoring=dict(type='bool', required=False, default=False),
        wait=dict(type='bool', required=False),
        state=dict(type='str', default='present', choices=['present', 'absent', 'dry-run']),
        role_arn=dict(type='str', required=False),
        support_role_arn=dict(type='str', required=False),
        operator_roles_prefix=dict(type='str', required=False),
        controlplane_iam_role=dict(type='str', required=False),
        worker_iam_role=dict(type='str', required=False),
        hosted_cp=dict(type=bool, required=False, default=False),
        oidc_config_id=dict(type=str, required=False),
        kms_key_arn=dict(type='str', required=False),
        admin_username=dict(type='str', required=False, default='admin'),
        admin_password=dict(type='str', required=False, no_log=True),
        tags=dict(type='dict', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    result = ocm_cluster_run(module)
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
