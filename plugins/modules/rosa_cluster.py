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

from ansible.module_utils.basic import *
import re
import time

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
        private_link=dict(type='bool', required=False),
        sts=dict(type='bool', required=False),
        aws_account_id=dict(type='str', required=False),
        disable_scp_checks=dict(type='bool', required=False),
        wait=dict(type='bool', required=False),
        state=dict(type='str', default='present', choices=['present','absent','dry-run', 'describe'])
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        commands=[],
        details="",
    )

    command_result = dict(
            reason="",
            command="",
            rc=None,
            stdout="",
            stderr=""
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
    wait = params.pop('wait')
    sts = params.pop('sts')
    aws_account_id = params.pop('aws_account_id')

    describe_args = [rosa, "describe", "cluster", "-c", name]
    if state == "absent":
        args = [rosa, "delete", "cluster", "-y", "-c", name]
    else:
        args = [rosa, "create", "cluster", "-y", "-c", name]

        if state == "dry-run": args.append("--dry-run")

    if sts:
        if not aws_account_id:
            module.fail_json(msg="must provide aws account id when using sts\n%s" % (command_result['stderr']), **result)
        args.extend(["--role-arn","arn:aws:iam::{}:role/ROSA-{}-install".format(aws_account_id, name)])
        args.extend(["--support-role-arn","arn:aws:iam::{}:role/ROSA-{}-support".format(aws_account_id, name)])
        args.extend(["--master-iam-role","arn:aws:iam::{}:role/ROSA-{}-control".format(aws_account_id, name)])
        args.extend(["--worker-iam-role","arn:aws:iam::{}:role/ROSA-{}-worker".format(aws_account_id, name)])
        args.extend(["--operator-iam-roles","aws-cloud-credentials,openshift-machine-api,arn:aws:iam::{}:role/ROSA-{}-machine-api".format(aws_account_id, name)])
        args.extend(["--operator-iam-roles","cloud-credential-operator-iam-ro-creds,openshift-cloud-credential-operator,arn:aws:iam::{}:role/ROSA-{}-cloud-credential".format(aws_account_id, name)])
        args.extend(["--operator-iam-roles","installer-cloud-credentials,openshift-image-registry,arn:aws:iam::{}:role/ROSA-{}-registry".format(aws_account_id, name)])
        args.extend(["--operator-iam-roles","cloud-credentials,openshift-ingress-operator,arn:aws:iam::{}:role/ROSA-{}-ingress".format(aws_account_id, name)])
        args.extend(["--operator-iam-roles","ebs-cloud-credentials,openshift-cluster-csi-drivers,arn:aws:iam::{}:role/ROSA-{}-csi-ebs".format(aws_account_id, name)])


    for param, value in params.items():
        if not value: continue
        if param == "multi_az": args.append("--multi-az")
        elif param == "enable_autoscaling": args.append("--enable-autoscaling")
        elif param == "private": args.append("--private")
        elif param == "private_link": args.append("--private-link")
        elif param == "disable_scp_checks": args.append("--disable_scp_checks")
        elif param == "region" or param == "profile":
            args.extend([argify(param), value])
            describe_args.extend([argify(param), value])
        else: args.extend([argify(param), value])

    # command_result['command'] = " ".join(args)
    # result['command'].append(" ".join(args))

    rc, stdout, stderr = module.run_command(describe_args)

    # save results
    command_result['command'] = " ".join(describe_args)
    result['details'] = cluster_details('stdout')
    command_result['reason'] = "check to see if cluster already exists"
    command_result['rc'], command_result['stdout'], command_result['stderr'] = rc, stdout, stderr
    result['commands'].append(command_result.copy())

    # if the cluster already exists
    if rc == 0:
        # delete on absent
        if state == "absent":
            result['changed'] = True
            command_result['rc'], command_result['stdout'], command_result['stderr'] = module.run_command(args)
            command_result['reason'] = "delete the cluster"
            command_result['command'] = " ".join(args)
            result['commands'].append(command_result)
            result['details'] = cluster_details(command_result['stdout'])
            if command_result['rc'] != 0:
                module.fail_json(msg="failed to delete cluster\n%s" % (command_result['stderr']), **result)
            if not wait:
                module.exit_json(**result)

    if rc == 1:
        # if the cluster doesn't exist, create it
        if state in ['present', 'dry-run'] and "There is no cluster with identifier or name" in stderr:
            if state == 'present':
                result['changed'] = True
            command_result['rc'], command_result['stdout'], command_result['stderr'] = module.run_command(args)
            command_result['command'] = " ".join(args)
            command_result['reason'] = "create the cluster"
            result['details'] = cluster_details(command_result['stdout'])
            result['commands'].append(command_result)
            if command_result['rc'] != 0:
                module.fail_json(msg="failed to create cluster\n%s" % (command_result['stderr']), **result)
        else:
            # unknown error, better fail.
            module.fail_json(msg="failed\n%s" % (command_result['stderr']), **result)

    if wait and state in ['present', 'absent']:
        ready = re.compile(r'State:\s+ready')
        done = None
        counter = 1
        while not done:
            command_result['reason'] = "wait for the cluster to be ready (attempt %s)" % (counter)
            command_result['rc'], command_result['stdout'], command_result['stderr'] = module.run_command(describe_args)
            command_result['command'] = " ".join(describe_args)
            result['commands'].append(command_result.copy())
            if command_result['rc'] == 0 and state == 'present' and ready.search(command_result['stdout']):
                # command_result['reason'] = command_result['reason'] + 'WE DID IT'
                done = "success"
            if command_result['rc'] == 1 and state == 'absent' and "There is no cluster with identifier or name" in command_result['stderr']:
                done = "success"
            counter += 1
            if counter > 60:
                done = "timeout"
            time.sleep(60)

        if done == 'timeout':
            result['details'] = cluster_details(command_result['stdout'])
            module.fail_json(msg="cluster did not finish provisioning within an hour\n%s" % (command_result['stderr']), **result)

    result['details'] = cluster_details(command_result['stdout'])
    module.exit_json(**result)

def cluster_details(stdout):
        if stdout == None: return ""
        ansi_escape = re.compile(r'\x1B')
        details = []
        for line in stdout.splitlines():
            if not ansi_escape.match(line):
                details.append(line)
        return "\n".join(details)

def argify(param):
    return "--" + param.replace("_", "-")

def main():
    run_module()


if __name__ == '__main__':
    main()