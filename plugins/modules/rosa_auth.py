#!/usr/bin/python

# Copyright: (c) 2021, Paul Czarkowski <pczarkowski@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
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
'''

EXAMPLES = r'''
# Pass in a message
- name: authenticate to rosa
  rosa_auth:
    token: XXXXXXXXXXXXXXXXX
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
'''

from ansible.module_utils.basic import *
import re

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        token=dict(type='str', required=True),
        state=dict(type='str', default="login", choices=['login','logout'])
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

    # token must be set
    token = module.params['token']
    if token == None or token == "":
      module.fail_json(msg='must provide a valid token', **result)

    ## check that rosa binary exists
    rosa = module.get_bin_path("rosa", required=True)
    if rosa == None:
          module.fail_json(msg='rosa cli not found in $PATH', **result)
    state = module.params['state']

    # build rosa command "rosa login" or "rosa logout"
    args = [rosa, state]

    if state == "login":
      args.extend(["--token", module.params['token']])

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