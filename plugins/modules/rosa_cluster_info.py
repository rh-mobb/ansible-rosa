#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from sys import stdout
__metaclass__ = type


DOCUMENTATION = r'''
---
module: rosa_cluster_info

short_description: Create Rosa Cluster

version_added: "1.0.0"

description: Creates ROSA (RedHat Openshift on AWS) Cluster

options:
    name:
        description: Name of the cluster. This will be used when generating a sub-domain for your cluster on openshiftapps.com.
        required: true
        type: str

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: get info about rosa cluster
  rosa_cluster_info:
    name: my-rosa-cluster
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
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        commands=[],
        cluster={},
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
    rosa_version = stdout.rstrip()[:7]
    if rc != 0:
        module.fail_json(msg='could not run rosa version', **result)
    if check_version.parse(rosa_version) < check_version.parse(MIN_ROSA_VERSION):
        module.fail_json(msg="rosa version %s does not meet minimum of %s" % (rosa_version, MIN_ROSA_VERSION), **result)

    params = module.params
    name = params.pop('name')


    describe_args = [rosa, "describe", "cluster", "-c", name, "--output", "json"]

    describe_rc, describe_stdout, describe_stderr = rosa_describe_cluster(module, rosa, name)
    result['commands'].append(commands(describe_rc, describe_stdout, describe_stderr, describe_args))
    if cluster_details(describe_stdout) == '':
        result['cluster'] = {}
    else:
        result['cluster'] = cluster_details(describe_stdout)
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

def commands(rc, stdout, stderr, args):
    cr = dict(
            command=" ".join(args),
            rc=rc,
            stdout=stdout,
            stderr=stderr
    )
    return cr

def main():
    run_module()

if __name__ == '__main__':
    main()
