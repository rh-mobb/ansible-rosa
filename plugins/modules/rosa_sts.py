#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: rosa_sts

short_description: Applies templates to support Red Hat OpenShift Service on AWS.

version_added: "1.0.0"

description: Applies templates to support Red Hat OpenShift Service on AWS.

options:
    token:
        description: The token provided by https://cloud.redhat.com/openshift/token/rosa
        required: false
        type: str
    type:
        description: The type of roles to create
        required: true
        type: str
        choices: ['account-roles','operator-roles', 'oidc-endpoint']
    state:
        description: only supports present right now
        required: false
        type: str
        choices: ['present']
        default: present

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
- name: initialize AWS account for rosa
  rosa_roles:
    type: account
    state: present


'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
'''

from ansible.module_utils.basic import *
import re
from packaging import version

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        token=dict(type='str', required=False),
        state=dict(type='str', default="present", choices=['present'])
        type=dict(type='str', required=True, choices=['account-roles','operator-roles','oidc-provider'])
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
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
    state = module.params['state']

    # check that rosa is minimum version
    # MIN_ROSA_VERSION
    rosa_version_cmd = [rosa, "version"]
    rc, stdout, stderr = module.run_command(rosa_version_cmd)
    rosa_version = stdout.rstrip()
    if rc != 0:
        module.fail_json(msg='could not run rosa version', **result)
    if version.parse(rosa_version) < version.parse(MIN_ROSA_VERSION):
        module.fail_json(msg="rosa version %s does not meet minimum of %s" % (rosa_version, MIN_ROSA_VERSION), **result)

    args = [rosa, "create", module.params['type']]
    if module.params['type'] == "account":
        a=b
    elif module.params['type'] == "oidc":
        a=b
    elif module.params['type'] == "operator":
        a=b
    else:
        module.fail_json(msg="failed to run")

    # token must be set
    token = module.params['token']
    if token != None and token != "":
      args.extend(["--token", module.params['token']])

    if state == "absent":
      args.append("--delete-stack")

    rc, out, err = module.run_command(args)

    if rc != 0:
        module.fail_json(msg="failed to run %s:\nstdout: %s\nstderr: %s" % (" ".join(args), out, err))

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()