#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from sys import stdout
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ocm_cluster

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
stdout: str
stderr: str
password: str
# These are examples of possible return values, and in general should use other names for return values.
'''

MIN_ROSA_VERSION = "1.2.23"

from ansible.module_utils.basic import *
from packaging import version as check_version
from semver import parse as semver_parse
from ansible.module_utils.ocm import OcmModule
from ansible.module_utils.ocm import OcmClusterModule
from ocm_client.rest import ApiException
import ocm_client
import time
import json
import string
import random

def run_module():
    # define available arguments/parameters a user can pass to the module
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
        enable_autoscaling=dict(type='bool', required=False),
        private=dict(type='bool', required=False),
        private_link=dict(type='bool', required=False),
        sts=dict(type='bool', required=False),
        aws_account_id=dict(type='str', required=False),
        disable_scp_checks=dict(type='bool', required=False),
        disable_workload_monitoring=dict(type='bool', required=False, default=False),
        wait=dict(type='bool', required=False),
        state=dict(type='str', default='present', choices=['present','absent','dry-run']),
        role_arn=dict(type='str', required=False),
        support_role_arn=dict(type='str', required=False),
        operator_roles_prefix=dict(type='str', required=False),
        controlplane_iam_role=dict(type='str', required=False),
        worker_iam_role=dict(type='str', required=False),
        hosted_cp=dict(type=bool, required=False, default=False),
        oidc_config_id=dict(type=str, required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        cluster=dict()
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # validate inputs
    name = module.params['name']
    cluster_id = ""

    if module.params['state'] != 'absent':
        if not module.params['operator_roles_prefix']:
            prefix = ''.join(random.choices(string.ascii_lowercase +
                                string.digits, k=4))
            module.params['operator_roles_prefix'] = "{}-{}".format(module.params['name'], prefix)

    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)

        # Check to see if there is a cluster of the same name
        if not cluster_id:
            cluster_id, err = OcmClusterModule.get_cluster_id(api_instance, name)
            if err:
                module.fail_json(err)
        if cluster_id:
            cluster_info, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
            if err:
                module.fail_json(err)
            if module.params['state'] == "present":
                result['cluster'] = cluster_info
                module.exit_json(**result)

        if module.params['state'] == "absent":
            deprovision = True
            dry_run = False
            try:
                api_instance.api_clusters_mgmt_v1_clusters_cluster_id_delete(cluster_id, deprovision=deprovision, dry_run=dry_run)
            except ApiException as e:
                err = "Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_delete: {}\n".format(e)
                module.fail_json(err)
            result['changed'] = True
            cluster_info, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
            if err:
                result['cluster'] = {}
            else:
                result['cluster'] = cluster_info
            module.exit_json(**result)

            # todo we should fetch the cluster status and return it vs just returning empty dict
            module.exit_json(**result)

        if module.params['state'] == "present":
            # check region is available
            # https://api.openshift.com/api/clusters_mgmt/v1/cloud_providers/aws/regions
            # check version is available
            # https://api.openshift.com/api/clusters_mgmt/v1/versions?page=1&search=enabled+%3D+%27true%27+AND+rosa_enabled+%3D+%27true%27+AND+channel_group+%3D+%27stable%27&size=100
            # get list of flavors
            # https://api.openshift.com/api/clusters_mgmt/v1/flavours/osd-4
                # "kind": "Flavour",
                # "name": "OpenShift Dedicated 4.X",
                # "id": "osd-4",
            # check machine types (POST)
            # https://api.openshift.com/api/clusters_mgmt/v1/aws_inquiries/machine_types?order=category+asc&page=1&size=100
                #   "aws": {
                #     "sts": {
                #       "role_arn": "arn:aws:iam::660250927410:role/ManagedOpenShift-Installer-Role"
                #     }
                #   },
                #   "region": {
                #     "kind": "CloudRegion",
                #     "id": "us-east-2"
                #   }
                # }
            # check quotas
            # https://api.openshift.com/api/accounts_mgmt/v1/organizations/1rkxPO7W12geIcRWITwI0I8VIQV/quota_cost?fetchRelatedResources=true&page=1&search=quota_id~%3D%27gpu%27&size=-1'

            cluster_info, err = OcmClusterModule.create_cluster(api_instance, module.params)
            result['cluster'] = cluster_info
            if err:
                module.fail_json("cluster:\n{}\n{}".format(cluster_info,err),**result)
            result['changed'] = True
            module.exit_json(**result)

        elif module.params['state'] == "dry-run":
            # result['details'] = '{"output": "successful dry-run"}'
            module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()
