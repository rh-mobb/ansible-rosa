from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import json
import random
import string
import time

import ocm_client
from ocm_client.exceptions import ApiException

from .ocm import OcmClusterModule, OcmModule


def lookup_cluster_by_name(api_instance, name):
    """Return (cluster_dict, error_message). cluster_dict is {} when not found."""
    cluster_id, err = OcmClusterModule.get_cluster_id(api_instance, name)
    if err:
        return None, err
    if not cluster_id:
        return {}, None
    cluster_info, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
    if err:
        return None, err
    return cluster_info, None


def ocm_cluster_info_run(module):
    """Implementation for ocm_cluster_info (and rosa_cluster_info body)."""
    result = dict(cluster={})
    if module.check_mode:
        return result

    name = module.params['name']
    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)
        cluster, err = lookup_cluster_by_name(api_instance, name)
        if err:
            module.fail_json(msg=err)
        result['cluster'] = cluster or {}
    return result


def _prepare_operator_roles_prefix(module):
    if module.params['state'] == 'absent':
        return
    if not module.params.get('operator_roles_prefix'):
        if module.params.get('_operator_roles_default') == 'rosa':
            module.params['operator_roles_prefix'] = module.params['name']
        else:
            prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            module.params['operator_roles_prefix'] = "{}-{}".format(
                module.params['name'], prefix
            )


def _wait_for_cluster(api_instance, name, state, timeout_seconds=3600, interval=60):
    """Poll OCM until cluster is ready (present) or gone (absent)."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        cluster_id, err = OcmClusterModule.get_cluster_id(api_instance, name)
        if err:
            return False, err
        if state == 'absent':
            if not cluster_id:
                return True, None
        else:
            if cluster_id:
                cluster, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
                if err:
                    return False, err
                if cluster.get('state') == 'ready':
                    return True, None
        time.sleep(interval)
    return False, None


def ocm_cluster_run(module):
    """Implementation for ocm_cluster module."""
    result = dict(changed=False, cluster={})
    if module.check_mode:
        return result

    if not module.params.get('_operator_roles_default'):
        module.params['_operator_roles_default'] = 'ocm'
    _prepare_operator_roles_prefix(module)

    name = module.params['name']
    state = module.params['state']

    if module.params.get('admin_password') and module.params.get('hosted_cp'):
        module.fail_json(msg="admin_password is not supported for hosted control-plane clusters")

    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)

        cluster_id, err = OcmClusterModule.get_cluster_id(api_instance, name)
        if err:
            module.fail_json(msg=err)

        if cluster_id and state == 'present':
            cluster_info, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
            if err:
                module.fail_json(msg=err)
            result['cluster'] = cluster_info
            return result

        if state == 'absent':
            if not cluster_id:
                return result
            try:
                api_instance.api_clusters_mgmt_v1_clusters_cluster_id_delete(
                    cluster_id, deprovision=True, dry_run=False
                )
            except ApiException as e:
                module.fail_json(
                    msg="Exception when calling DefaultApi->api_clusters_mgmt_v1_clusters_cluster_id_delete: {}\n".format(e)
                )
            result['changed'] = True
            if module.params.get('wait'):
                ok, wait_err = _wait_for_cluster(api_instance, name, 'absent')
                if wait_err:
                    module.fail_json(msg=wait_err)
                if not ok:
                    module.fail_json(msg="cluster did not finish deletion within an hour")
            cluster_info, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
            result['cluster'] = {} if err else cluster_info
            return result

        if state == 'dry-run':
            return result

        if state == 'present':
            if not module.params.get('subnet_ids'):
                module.fail_json(msg="subnet_ids is required for cluster creation")
            cluster_info, err = OcmClusterModule.create_cluster(api_instance, module.params)
            result['cluster'] = cluster_info
            if err:
                module.fail_json(msg="cluster:\n{}\n{}".format(cluster_info, err), **result)
            result['changed'] = True
            if module.params.get('wait'):
                ok, wait_err = _wait_for_cluster(api_instance, name, 'present')
                if wait_err:
                    module.fail_json(msg=wait_err)
                if not ok:
                    module.fail_json(msg="cluster did not finish provisioning within an hour", **result)
                cluster_id, _ = OcmClusterModule.get_cluster_id(api_instance, name)
                if cluster_id:
                    cluster_info, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
                    if not err:
                        result['cluster'] = cluster_info
            return result

    module.fail_json(msg="Unsupported state: {}".format(state))


def rosa_params_to_ocm(module):
    """Map rosa_cluster module params to ocm_cluster create payload defaults."""
    ocm = module.params.copy()
    if ocm.get('enable_autoscaling') and not (ocm.get('min_replicas') and ocm.get('max_replicas')):
        module.fail_json(
            msg="enable_autoscaling requires min_replicas and max_replicas",
            changed=False,
            commands=[],
            details=None,
        )
    if ocm.get('sts') and not ocm.get('aws_account_id'):
        from .ocm import aws_account_id as ocm_aws_account_id
        try:
            ocm['aws_account_id'] = ocm_aws_account_id()
        except Exception:
            module.fail_json(
                msg="must provide aws account id when using sts",
                changed=False,
                commands=[],
                details=None,
            )
    ocm.setdefault('hosted_cp', False)
    ocm.setdefault('tags', {})
    ocm.setdefault('disable_scp_checks', False)
    ocm.setdefault('disable_workload_monitoring', False)
    ocm.setdefault('private', False)
    ocm.setdefault('private_link', False)
    ocm.setdefault('multi_az', False)
    return ocm


def _synthetic_command(name, cluster, rc=0, err=''):
    return dict(
        command="ocm_cluster(name={})".format(name),
        rc=rc,
        stdout=json.dumps(cluster) if cluster else '',
        stderr=err or '',
    )


def rosa_cluster_info_run(module):
    result = dict(commands=[], cluster={})
    if module.check_mode:
        return result

    name = module.params['name']
    core = ocm_cluster_info_run(module)
    result['cluster'] = core.get('cluster', {})
    result['commands'].append(_synthetic_command(name, result['cluster']))
    return result


def rosa_cluster_run(module):
    result = dict(changed=False, commands=[], details=None)
    if module.check_mode:
        return result

    state = module.params['state']
    name = module.params['name']
    ocm_params = rosa_params_to_ocm(module)
    for key, value in ocm_params.items():
        module.params[key] = value
    module.params['_operator_roles_default'] = 'rosa'

    if state == 'describe':
        info = ocm_cluster_info_run(module)
        result['details'] = info.get('cluster') or {}
        result['commands'].append(_synthetic_command(name, result['details']))
        return result

    # Reuse ocm cluster driver with rosa operator-role defaulting and result shaping.
    module.params = ocm_params
    if state == 'dry-run':
        result['details'] = {'output': 'successful dry-run'}
        result['commands'].append(
            dict(
                command="ocm_cluster(state=dry-run,name={})".format(name),
                rc=0,
                stdout=result['details']['output'],
                stderr='',
                reason='dry-run',
            )
        )
        return result

    core = ocm_cluster_run(module)
    result['changed'] = core.get('changed', False)
    result['details'] = core.get('cluster') or {}
    verb = 'delete the cluster' if state == 'absent' else 'create cluster'
    result['commands'].append(
        dict(
            reason=verb,
            command="ocm_cluster(state={},name={})".format(state, name),
            rc=0,
            stdout=json.dumps(result['details']) if result['details'] else '',
            stderr='',
        )
    )
    return result
