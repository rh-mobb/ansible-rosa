#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from sys import stdout
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

MIN_ROSA_VERSION = "1.2.22"

from ansible.module_utils.basic import *
from packaging import version as check_version
from semver import parse as semver_parse
import time
import json

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
        state=dict(type='str', default='present', choices=['present','absent','dry-run', 'describe']),
        role_arn=dict(type='str', required=False),
        support_role_arn=dict(type='str', required=False),
        controlplane_iam_role=dict(type='str', required=False),
        worker_iam_role=dict(type='str', required=False),
        hosted_cp=dict(type=bool, required=False),
        oidc_config_id=dict(type=str, required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        commands=[],
        details=None,
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

    # check that rosa is minimum version
    # MIN_ROSA_VERSION
    rosa_version_cmd = [rosa, "version"]
    # rosa_version_cmd = [rosa, "version", "|", "head", "-1"]
    rc, stdout, stderr = module.run_command(rosa_version_cmd)
    rosa_version = stdout.rstrip().split('\n')[0]
    if rc != 0:
        module.fail_json(msg='could not run rosa version', **result)
    if check_version.parse(rosa_version) < check_version.parse(MIN_ROSA_VERSION):
        module.fail_json(msg="rosa version %s does not meet minimum of %s" % (rosa_version, MIN_ROSA_VERSION), **result)

    params = module.params
    state = params.pop('state')
    name = params.pop('name')
    wait = params.pop('wait')
    sts = params.pop('sts')
    aws_account_id = params.pop('aws_account_id')
    cluster_version = params['version']
    cluster_semver = semver_parse(cluster_version)
    sts_version = str(cluster_semver['major']) + "." + str(cluster_semver['minor'])

    describe_args = [rosa, "describe", "cluster", "-c", name, "--output", "json"]
    if state == "absent":
        args = [rosa, "delete", "cluster", "-y", "-c", name]
    else:
        args = [rosa, "create", "cluster", "-y", "-c", name]

        if state == "dry-run":
            args.append("--dry-run")

        if sts:
            if not aws_account_id:
                module.fail_json(msg="must provide aws account id when using sts\n", **result)
            args.append("--sts")
            args.extend(['--mode', 'auto'])

        for param, value in params.items():
            if not value: continue
            if param == "multi_az": args.append("--multi-az")
            elif param == "hosted_cp": args.append("--hosted-cp")
            elif param == "enable_autoscaling": args.append("--enable-autoscaling")
            elif param == "private": args.append("--private")
            elif param == "private_link": args.append("--private-link")
            elif param == "disable_scp_checks": args.append("--disable-scp-checks")
            elif param == "disable_workload_monitoring": args.append("--disable-workload-monitoring")
            elif param == "region" or param == "profile":
                args.extend([argify(param), value])
                describe_args.extend([argify(param), value])
            else: args.extend([argify(param), value])

    describe_rc, describe_stdout, describe_stderr = rosa_describe_cluster(module, rosa, name)

    # if the cluster already exists
    if describe_rc == 0:
        # delete on absent
        if state == "absent":
            result['changed'] = True
            rc, stdout, stderr = module.run_command(args)
            reason = "delete the cluster"
            command = " ".join(args)
            result['commands'].append(commands(rc, stdout, stderr, reason, args))
            if rc != 0:
                module.fail_json(msg="failed to delete cluster\n%s" % (stderr), **result)
            if not wait:
                module.exit_json(**result)

    if describe_rc == 1:
        # create sts account roles
        # if sts:
        #     print("Create Account Roles")
        #     create_account_roles = [rosa, "create", "account-roles", "--mode", "auto", "--yes"]
        #     if state == "present":
        #         rc = 1
        #         while rc != 0:
        #             rc, stdout, stderr = module.run_command(create_account_roles)
        #             result['commands'].append(commands(rc, stdout, stderr, 'create sts account roles', create_account_roles))
        #             if rc != 0:
        #                 if "Throttling: Rate exceeded" in stderr:
        #                     time.sleep(60)
        #                     continue
        #                 module.fail_json(msg="failed to create account roles\n%s" % (stderr))
        #     elif state == "dry-run":
        #         result['commands'].append(commands(0, "skipped due to dry-run", None, 'create sts account roles', create_account_roles))
        # print ("Create Cluster")
        # if the cluster doesn't exist, create it
        if state in ['present', 'dry-run'] and "There is no cluster with identifier or name" in describe_stderr:
            if state == 'present':
                result['changed'] = True
            rc, stdout, stderr = module.run_command(args)
            # result['details'] = cluster_details(stdout)
            result['commands'].append(commands(rc, stdout, stderr, 'create cluster', args))
            if rc != 0:
                module.fail_json(msg="failed to create cluster\n%s" % (stderr), **result)
        else:
            # unknown error, better fail.
            module.fail_json(msg="failed for unknown reason\n%s" % (describe_stderr), **result)

    if wait and state in ['present', 'absent']:
        # ready = re.compile(r'State:\s+ready')
        done = None
        counter = 1
        while not done:
            time.sleep(60)
            rc, stdout, stderr = rosa_describe_cluster(module, rosa, name)
            if rc == 0 and state == 'present' and cluster_details(stdout)['ready']:
                done = "success"
            if rc == 1 and state == 'absent' and "There is no cluster with identifier or name" in stderr:
                done = "success"
            counter += 1
            if counter > 60:
                done = "timeout"

        if done == 'timeout':
            result['details'] = cluster_details(stdout)
            module.fail_json(msg="cluster did not finish provisioning within an hour\n%s" % (command_result['stderr']), **result)

    if state == "present":
        rc, stdout, stderr = rosa_describe_cluster(module, rosa, name)
        result['details'] = cluster_details(stdout)
    elif state == "dry-run":
        result['details'] = '{"output": "successful dry-run"}'
    module.exit_json(**result)

def rosa_describe_cluster(module, rosa, name):
    args = [rosa, "describe", "cluster", "-c", name, "--output", "json"]
    rc, stdout, stderr = module.run_command(args)
    return rc, stdout, stderr

def cluster_details(stdout):
    try:
        return json.loads(stdout)
    except:
        return stdout

def commands(rc, stdout, stderr, reason, args):
    cr = dict(
            reason=reason,
            command=" ".join(args),
            rc=rc,
            stdout=stdout,
            stderr=stderr
    )
    return cr


def argify(param):
    return "--" + param.replace("_", "-")

def main():
    run_module()


if __name__ == '__main__':
    main()
