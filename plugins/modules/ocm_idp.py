#!/usr/bin/python

# Copyright: (c) 2023 Paul Czarkowski
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ocm_idp

short_description: This module manages IDP for OCM / ROSA clusters

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This module manages IDP for OCM / ROSA clusters

options:
    name:
        description: The name of the IDP
        required: true
        type: str
    type:
        description: type of the IDP (currently only accepts 'htpasswd')
        required: true
        type: str
    cluster_name:
        description: name of the OCM cluster (one of this or cluster_id needed)
        required: false
        type: str
    cluster_id:
        description: ID of the OCM cluster (one of this or clustr_name is needed)
        required: false
        type: str
    username:
        description: username to set for htpasswd
        required: false
        type: str
    password:
        description: password to set for htpasswd
        required: false
        type: str

# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - rh_mobb.ansible_rosa.my_doc_fragment_name

author:
    - Paul Czarkowski (@paulczar)
'''

EXAMPLES = r'''
# create a htpasswd idp
- name: create htpasswd idp
    rh_mobb.ansible_rosa.ocm_idp:
      name: admin
      password: 'admin1234567890!'
      username: admin
      type: htpasswd
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
name:
    description: name of the IDP
    type: str
    returned: always
    sample: 'admin'
password:
    description: htpasswd password (is always empty string for security)
    type: str
    returned: when idp type is htpasswd
    sample: ''
username:
    description: htpasswd username
    type: str
    returned:  when idp type is htpasswd
    sample: 'admin'
type:
    description: type of IDP
    type: str
    returned: always
    sample: 'HTPasswdIdentityProvider'
'''

from ansible.module_utils.basic import AnsibleModule
import ocm_client
from ocm_client.rest import ApiException
import os
from pathlib import Path
import json
import requests

OCM_JSON = os.getenv('OCM_JSON', str(Path.home()) + "/.config/ocm/ocm.json")
OCM_HOST = "https://api.openshift.com"

def ocm_authenticate():
    f = open(OCM_JSON,)
    user = json.load(f)
    auth = (user['client_id'], user['access_token'])
    params = {
        "grant_type": "refresh_token",
        "refresh_token": user['refresh_token']
    }
    response = requests.post(user['token_url'], auth=auth, data=params)
    access_token = response.json()['access_token']

    configuration = ocm_client.Configuration(
        host = OCM_HOST
    )

    configuration.access_token = access_token
    return configuration

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        cluster_name=dict(type='str', required=False),
        cluster_id=dict(type='str', required=False),
        name=dict(type='str', required=True),
        type=dict(type='str', required=True),
        username=dict(type='str', required=False),
        password=dict(type='str', required=False),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        # response='',
        name='',
        type='',
        username='',
        password='',
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

    # check complex dependencies
    if module.params['type'] == 'htpasswd':
        if not module.params['username']:
            module.fail_json(msg='must provide "username" for "htpasswd"', **result)
        if not module.params['password']:
            module.fail_json(msg='must provide "password" for "htpasswd"', **result)

    if not (module.params['cluster_name']) and (not module.params['cluster_id']):
        module.fail_json(msg='must provide "cluster_name" or "cluster_id"', **result)
    if (module.params['cluster_name']) and (module.params['cluster_id']):
        module.fail_json(msg='cannot provide both "cluster_name" or "cluster_id"', **result)

    # with the easy checks out of the way, log into ocm so we can API
    cluster_id = module.params['cluster_id']
    with ocm_client.ApiClient(ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)

        # First, fetch the cluster_id if we don't already have it
        if not cluster_id:
            search = "name = '{}'".format(module.params['cluster_name'])
            try:
                api_response = api_instance.api_clusters_mgmt_v1_clusters_get(search=search, size="1")
            except ApiException as e:
                module.fail_json("Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_get: %s\n" % e)
            cluster_id = api_response.items[0].id
            # result['cluster_id'] = api_response.items[0].id

        # Fetch identity providers
        try:
            api_request = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_get(cluster_id,page=1,size=-1)
            existing_idps = api_request.items
        except ApiException as e:
            module.fail_json("Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_get: %s\n" % e)

        if module.params['type'] == 'htpasswd':
            # find existing idp
            if existing_idps:
                for idp in existing_idps:
                    if idp.type == 'HTPasswdIdentityProvider':
                        existing_htpasswd = idp
                        break
                # if pre-existing htpasswd idp we must error
                if existing_htpasswd:
                    if existing_htpasswd.name == "admin":
                        result['name'] = existing_htpasswd.name
                        result['type'] = existing_htpasswd.type
                        result['username'] = existing_htpasswd.htpasswd.username
                        result['password'] = ''
                        module.exit_json(**result)
                    else:
                        module.fail_json("an htpasswd IDP called {} already exists. OCM only supports a single IDP.".format(existing_htpasswd.name))
            # construct the htpasswd object
            ht_passwd_idp = ocm_client.HTPasswdIdentityProvider(
                username = module.params['username'],
                password = module.params['password'],
            )
            identity_provider = ocm_client.IdentityProvider(
                kind = 'IdentityProvider',
                mapping_method = 'claim',
                name = module.params['name'],
                type = 'HTPasswdIdentityProvider',
                htpasswd = ht_passwd_idp,
            )
            # create htpasswd
            idp_id = module.params['name']
            try:
                api_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_post(cluster_id, identity_provider=identity_provider)
            except ApiException as e:
                module.fail_json("Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_post: %s\n" % e)
            # result['response'] = api_response.to_str()
            result['name'] = api_response.name
            result['type'] = api_response.type
            result['username'] = api_response.htpasswd.username
            result['password'] = ''
            result['changed'] = True
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
