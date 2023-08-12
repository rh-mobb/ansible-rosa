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

# from botocore.exceptions import BotoCoreError
# from botocore.exceptions import ClientError
import boto3
# except ImportError:
#     pass  # Handled by AnsibleAWSModule

OCM_CONFIG_LOCATIONS = [
    "/Library/Application\ Support/ocm/ocm.json",
    "/.config/ocm/ocm.json"
]

OCM_HOST = "https://api.openshift.com"

DEFAULT_COMPUTE_NODES_MULTI_AZ = 3
DEFAULT_COMPUTE_NODES_SINGLE_AZ = 2

# TODO get these from OCM API, vs hard coding them.
OPERATOR_ROLES_CLASSIC = [
    dict(
        name = "cloud-credential-operator-iam-ro-creds",
        namespace = "openshift-cloud-credential-operator",
    ),
    dict(
        name = "installer-cloud-credentials",
        namespace = "openshift-image-registry",
    ),
    dict(
        name = "cloud-credentials",
        namespace = "openshift-ingress-operator",
    ),
    dict(
        name = "ebs-cloud-credentials",
        namespace = "openshift-cluster-csi-drivers",
    ),
    dict(
        name = "cloud-credentials",
        namespace = "openshift-cloud-network-config-controller",
    ),
    dict(
        name = "aws-cloud-credentials",
        namespace = "openshift-machine-api",
    ),
]

OPERATOR_ROLES_HCP = [
    dict(
        name = "ebs-cloud-credentials",
        namespace = "openshift-cluster-csi-drivers",
    ),
    dict(
        name = "cloud-credentials",
        namespace = "openshift-cloud-network-config-controller",
    ),
    dict(
        name = "kube-controller-manager",
        namespace = "kube-system",

    ),
    dict(
        name = "capa-controller-manager",
        namespace = "kube-system",

    ),
    dict(
        name = "control-plane-operator",
        namespace = "kube-system",

    ),
    dict(
        name = "kms-provider",
        namespace = "kube-system",

    ),
    dict(
        name = "installer-cloud-credentials",
        namespace = "openshift-image-registry",
    ),
    dict(
        name = "cloud-credentials",
        namespace = "openshift-ingress-operator",
    ),
]

def find_ocm_config():
    config = os.getenv('OCM_JSON', None)
    if not config:
        for path in OCM_CONFIG_LOCATIONS:
            check = os.path.join(Path.home(),path)
            if os.path.isfile(check):
                return check
    return config

def rosa_creator_arn():
    client = boto3.client("sts")
    return client.get_caller_identity()["Arn"]

def rosa_compute_nodes(multi_az, count):
    if count:
        return count
    if multi_az:
        return DEFAULT_COMPUTE_NODES_MULTI_AZ
    else:
        return DEFAULT_COMPUTE_NODES_SINGLE_AZ

def getAvailibilityZoneForSubnets(subnet_ids, region):
    if type(subnet_ids) is str:
        subnet_ids = subnet_ids.join(',')
    if type(subnet_ids) is list:
        if len(subnet_ids) == 0:
            return None
    availability_zones = []
    try:
        # Create a Boto3 EC2 client
        ec2_client = boto3.client('ec2', region_name=region)
        # Describe the subnet using the subnet_id
        response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        # Extract the availability zone from the response
        for az in response['Subnets']:
            if az['AvailabilityZone'] not in availability_zones:
                availability_zones.append(az['AvailabilityZone'])
    except Exception as e:
        print(f"Error: {e}")
        return None, e
    return availability_zones, None

def populateOperatorRoles(prefix, account_id, hcp):
    source_roles = OPERATOR_ROLES_HCP if hcp else OPERATOR_ROLES_CLASSIC
    operator_roles = []
    for role_contents in source_roles:
        role = "{}-{}-{}".format(prefix,role_contents['namespace'],role_contents['name'])
        arn = "arn:aws:iam::{}:role/{}".format(account_id,role[:64])
        operator_role = ocm_client.OperatorIAMRole(
            name = role_contents['name'],
            namespace = role_contents['namespace'],
            role_arn = arn,
        )
        operator_roles.append(operator_role)
    return operator_roles

def api_visibility(private):
    if private:
        return ocm_client.ClusterAPI(
            listening = 'internal'
        )
    return ocm_client.ClusterAPI()

#class OcmModule(object):
#    import requests
#import ocm_client

class OcmModule(object):
    def ocm_authenticate():
        config_path = find_ocm_config()
        if config_path is not None:
            with open(config_path) as f:
                user = json.load(f)
                auth = (user['client_id'], user['access_token'])
                params = {
                    "grant_type": "refresh_token",
                    "refresh_token": user['refresh_token']
                }
                response = requests.post(user['token_url'], auth=auth, data=params)
                access_token = response.json()['access_token']

                configuration = ocm_client.Configuration(
                    host=OCM_HOST,
                    api_key={
                        'authorization': 'Bearer ' + access_token
                    }
                )
                return configuration
        else:
            return None, "OCM configuration file not found."  

    """
    def ocm_authenticate():
        f = open(find_ocm_config(),)
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
    """

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

    def create_cluster(api_instance, params):
        availibility_zones, err = getAvailibilityZoneForSubnets(params['subnet_ids'].split(','), params['region'])
        if err:
            return None, err

        if not params['compute_nodes']:
            if params['multi_az']:
                params['compute_nodes'] = 3
            else:
                params['compute_nodes'] = 2
        additional_trust_bundle = None
        if params['additional_trust_bundle_file']:
            additional_trust_bundle = Path(params['additional_trust_bundle_file']).read_text()
        if params['oidc_config_id']:
            oidc_config, err = OcmOidcConfig.get(api_instance, params['oidc_config_id'])
            if err:
                return None, err
        else:
            oidc_config = None
        instance_iam_roles = ocm_client.InstanceIAMRoles(
            worker_role_arn = params['worker_iam_role'],
        )
        if not params['hosted_cp']:
            instance_iam_roles.master_role_arn = params['controlplane_iam_role']
        cluster = ocm_client.Cluster(
            api = api_visibility((params['private_link'] or params['private'])),
            aws = ocm_client.AWS(
                sts = ocm_client.STS(
                    enabled = params['sts'],
                    auto_mode = False, #p arams['hosted_cp'],
                    instance_iam_roles = instance_iam_roles,
                    oidc_config = oidc_config,
                    # operator_role_prefix = params['operator_roles_prefix'],
                    operator_iam_roles = populateOperatorRoles(params['operator_roles_prefix'],params['aws_account_id'],params['hosted_cp']),
                    role_arn = params['role_arn'],
                    support_role_arn = params['support_role_arn'],
                ),
                account_id = params['aws_account_id'],
                # audit_log
                etcd_encryption = ocm_client.AwsEtcdEncryption(),
                private_link = params['private_link'],
                subnet_ids = params['subnet_ids'].split(','),
                # todo tags = params['tags']
            ),
            ccs = ocm_client.CCS(
                disable_scp_checks = params['disable_scp_checks'],
                enabled = True,
            ),
            # dns = ocm_client.DNS(),
            additional_trust_bundle = additional_trust_bundle,
            cloud_provider = ocm_client.CloudProvider(
                name = 'aws'
            ),
            # todo disable_user_workload_monitoring = params['disable_user_workload_monitoring']
            etcd_encryption = False,
            flavour = ocm_client.Flavour(
                id = 'osd-4'
            ),
            hypershift = ocm_client.Hypershift(
                enabled = params['hosted_cp']
            ),
            multi_az = params['multi_az'],
            name = params['name'],
            network = ocm_client.Network(
                host_prefix = params['host_prefix'],
                machine_cidr = params['machine_cidr'],
                pod_cidr = params['pod_cidr'],
                service_cidr = params['service_cidr'],
            ),
            # node_drain_grace_period = 15
            # node_pools
            # TODO verify and build dynamically
            nodes = ocm_client.ClusterNodes(
                compute = rosa_compute_nodes(params['multi_az'], params['compute_nodes']),
                compute_machine_type = ocm_client.MachineType(
                    id = params['compute_machine_type'] or 'm5.xlarge'
                ),
                availability_zones = availibility_zones
            ),
            product = ocm_client.Product(
                id = 'rosa'
            ),
            properties = dict(
                rosa_creator_arn = rosa_creator_arn(),
                rosa_provisioner = 'ocm-ansible-module'
            ),
            proxy = ocm_client.Proxy(
                http_proxy = params['http_proxy'],
                https_proxy = params['https_proxy'],
                no_proxy = params['no_proxy'],
            ),
            region = ocm_client.CloudRegion(
                id = params['region'],
            ),
            # todo calculate
            version = ocm_client.Version(
                id = "openshift-v{}".format(params['version']),
                channel_group = "stable",
            ),
        )

        try:
            cluster_create = api_instance.api_clusters_mgmt_v1_clusters_post(cluster=cluster)
        except ApiException as e:
            return cluster.to_dict(), "Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_post: {}\n".format(e)
        return cluster_create.to_dict(), None
        # return cluster.to_dict(), None

    @staticmethod
    def authenticate_ocm():
        ocm_module = OcmModule() 
        return ocm_module.ocm_authenticate()  

    @staticmethod
    def get_ocm_api_instance():
        configuration = OcmClusterModule.authenticate_ocm()
        if configuration:
            return ocm_client.DefaultApi(ocm_client.ApiClient(configuration))
        else:
            return None, "Failed to authenticate with OCM."
        

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

class OcmOidcConfig:
    def get(api_instance, oidc_config_id):
        try:
            api_response = api_instance.api_clusters_mgmt_v1_oidc_configs_oidc_config_id_get(oidc_config_id)
        except ApiException as e:
            err = "Exception when calling DefaultApi->api_clusters_mgmt_v1_oidc_configs_oidc_config_id_get: {}".format(e)
            return None, err
        return api_response, None

