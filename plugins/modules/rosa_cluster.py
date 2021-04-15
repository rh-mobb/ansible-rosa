#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
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
'''

EXAMPLES = r'''
- name: Create a rosa cluster using all defaults
  rosa_cluster:
    name: my-rosa-cluster
    state: present

- name: delete a rosa cluster
  rosa_cluster:
    name: my-rosa-cluster
    state: absent


'''

RETURN = r'''
stdout: str
stderr: str
password: str
# These are examples of possible return values, and in general should use other names for return values.
'''

from ansible.module_utils.basic import *
import re

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        region=dict(type='str', required=False),
        version=dict(type='str', required=False),
        channel_group=dict(type='str', required=False),
        compute_machine_type=dict(type='str', required=False),
        compute_nodes=dict(type='int', required=False),
        min_replicas=dict(type='int', required=False),
        max_replicas=dict(type='int', required=False),
        machine_cidr=dict(type='str', required=False),
        service_cidr=dict(type='str', required=False),
        pod_cidr=dict(type='str', required=False),
        host_prefix=dict(type='int', required=False),
        subnet_ids=dict(type='str', required=False),
        multi_az=dict(type='bool', required=False),
        enable_autoscaling=dict(type='bool', required=False),
        private=dict(type='bool', required=False),
        disable_scp_checks=dict(type='bool', required=False),
        state=dict(type='str', default='present', choices=['present','absent','dry-run'])
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        rc=None,
        stdout=None,
        stderr=None,
        command=[],
        details="",
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

    # check that rosa binary exists
    rosa = module.get_bin_path("rosa", required=True)
    if rosa == None:
          module.fail_json(msg='rosa cli not found in $PATH', **result)

    params = module.params
    state = params.pop('state')
    name = params.pop('name')
    if state == "absent":
        args = [rosa, "delete", "cluster", "-y", "-c", name]
    else:
        args = [rosa, "create", "cluster", "-c", name]

        if state == "dry-run": args.append("--dry-run")
        for param, value in params.items():
            if not value: continue
            if param == "multi_az": args.append("--multi-az")
            elif param == "enable_autoscaling": args.append("--enable-autoscaling")
            elif param == "private": args.append("--private")
            elif param == "disable_scp_checks": args.append("--dsiable_scp_checks")
            else: args.extend([argify(param), value])

    result['command'] = args
    result['rc'], result['stdout'], result['stderr'] = module.run_command(args)

    # TODO implement idempotency for create/delete
    if result['rc'] != 0:
        if state == "present":
            module.fail_json(msg="failed to create cluster\n%s" % (result['stderr']), **result)
        if state == "absent":
            module.fail_json(msg="failed to delete cluster\n%s" % (result['stderr']), **result)
        if state == "dry-run":
            module.fail_json(msg="failed to dry-run create of cluster\n%s" % (result['stderr']), **result)

    if state != "dry-run":
        result['changed'] = True

    if state == "present":
        stdout = result['stdout'].splitlines()
        stdout_filtered = '\n'.join(
            list(filter(lambda line: not line.startswith('['), stdout))
        )
        result['details'] = stdout_filtered

    module.exit_json(**result)

def argify(param):
    return "--" + param.replace("_", "-")

def main():
    run_module()


if __name__ == '__main__':
    main()