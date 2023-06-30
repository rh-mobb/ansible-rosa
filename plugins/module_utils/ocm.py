#!/usr/bin/env python

# Copyright 2023 Paul Czarkowski <pczarkow@redhat.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import ocm_client
from ocm_client.rest import ApiException
import os
from pathlib import Path
import json
import requests

OCM_JSON = os.getenv('OCM_JSON', str(Path.home()) + "/.config/ocm/ocm.json")
OCM_HOST = "https://api.openshift.com"

class OcmModule(object):
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


class OcmClusterModule(object):
    def get_cluster_id(api_instance, cluster_name):
        search = "name = '{}'".format(cluster_name)
        try:
            api_response = api_instance.api_clusters_mgmt_v1_clusters_get(search=search, size="1")
        except ApiException as e:
            return None, "Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_get: {}\n".format(e)
        if len(api_response.items) > 0:
            return api_response.items[0].id, None
        else:
            return None, None
            # module.fail_json("Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_get: %s\n" % e)

    def get_cluster_info(api_instance, cluster_id):
        try:
            cluster_info = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_get(cluster_id)
        except ApiException as e:
            return None, "Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_get: {}\n".format(e)
        # if not len(cluster_info.to_dict()) == 1:
        #     return None, "Incorrect number of cluster results:\n {}".format(cluster_info.to_str())
        return cluster_info.to_dict(), None


class OcmIdpModule(object):
    def get_cluster_idps(api_instance, cluster_id):
        try:
            api_request = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_get(cluster_id,page=1,size=-1)
        except ApiException as e:
            return None, "Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_get: %s\n" % e
            # module.fail_json("Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_get: %s\n" % e)
        return api_request.items, None

    def get_existing_htpasswd_idps(existing_idps):
        for idp in existing_idps:
            if idp.type == 'HTPasswdIdentityProvider':
                return idp

    def htpasswd_idp_builder(username, password, name):
        idp = ocm_client.IdentityProvider(
            kind = 'IdentityProvider',
            mapping_method = 'claim',
            name = name,
            type = 'HTPasswdIdentityProvider',
            htpasswd = ocm_client.HTPasswdIdentityProvider(
                username = username,
                password = password,
            )
        )
        return idp

    def create_htpasswd_idp(api_instance, cluster_id, identity_provider):
        try:
            api_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_post(cluster_id, identity_provider=identity_provider)
        except ApiException as e:
            return None, "Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_identity_providers_post: {}}\n".format(e)
        return api_response, None

    def create_cluster_role(api_instance, cluster_id, role, username):
        group_id = role
        user = ocm_client.User(
            kind = 'User',
            id = username
        )
        try:
            create_role = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_groups_group_id_users_post(cluster_id, group_id, user=user)
        except ApiException as e:
            if e.body.id not in ["400"]:
                return None, "Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_groups_group_id_users_post: {}\n".format(e)
        return create_role, None
