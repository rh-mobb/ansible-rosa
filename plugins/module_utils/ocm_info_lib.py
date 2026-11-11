from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import json

import ocm_client
from ocm_client.exceptions import ApiException

from .ocm import (
    OcmClusterModule,
    OcmIdpModule,
    OcmModule,
    _decode_ocm_http_response,
    _escape_ocm_search_literal,
)


def _synthetic_command(action, cluster, payload, rc=0, stderr='', machine_pool=None):
    cmd = "ocm:{}(cluster={}".format(action, cluster)
    if machine_pool:
        cmd += ",machine_pool={}".format(machine_pool)
    cmd += ")"
    return dict(
        command=cmd,
        rc=rc,
        stdout=json.dumps(payload) if payload is not None else '',
        stderr=stderr or '',
    )


def _list_page_from_response(http_response):
    if http_response.status == 404:
        return [], {}
    payload = _decode_ocm_http_response(http_response)
    if _is_error_payload(payload):
        return [], payload
    items = payload.get('items') or []
    return items, payload


def resolve_cluster(api_instance, cluster_ref):
    """Return (cluster_id, cluster_dict, error_message)."""
    cluster_id, err = OcmClusterModule.get_cluster_id(api_instance, cluster_ref)
    if err:
        return None, None, err
    if cluster_id:
        cluster, err = OcmClusterModule.get_cluster_info(api_instance, cluster_id)
        if err:
            return None, None, err
        return cluster_id, cluster, None
    try:
        http_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_get_without_preload_content(
            cluster_ref
        )
        cluster = _decode_ocm_http_response(http_response)
    except ApiException as e:
        if e.status == 404:
            return None, None, None
        return None, None, str(e)
    cluster_id = cluster.get('id') or cluster_ref
    return cluster_id, cluster, None


def fetch_autoscaler(api_instance, cluster_id):
    try:
        http_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_autoscaler_get_without_preload_content(
            cluster_id
        )
    except ApiException as e:
        if e.status == 404:
            return {}, None
        return None, "Exception when calling autoscaler get: {}\n".format(e)
    return _decode_ocm_http_response(http_response), None


def _is_error_payload(payload):
    return isinstance(payload, dict) and payload.get('kind') == 'Error'


def _machine_pool_from_response(http_response):
    if http_response.status == 404:
        return None, None
    payload = _decode_ocm_http_response(http_response)
    if _is_error_payload(payload):
        return None, None
    return payload, None


def fetch_machine_pool(api_instance, cluster_id, machine_pool):
    try:
        http_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_machine_pools_machine_pool_id_get_without_preload_content(
            cluster_id,
            machine_pool,
        )
        payload, err = _machine_pool_from_response(http_response)
        if err:
            return None, err
        if payload:
            return payload, None
    except ApiException as e:
        if e.status != 404:
            return None, "Exception when calling machine pool get: {}\n".format(e)
    try:
        http_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_node_pools_node_pool_id_get_without_preload_content(
            cluster_id,
            machine_pool,
        )
        payload, err = _machine_pool_from_response(http_response)
        if err:
            return None, err
        return payload or {}, None
    except ApiException as e:
        if e.status == 404:
            return {}, None
        return None, "Exception when calling node pool get: {}\n".format(e)


def build_admin_info(api_instance, cluster_id, cluster):
    api_url = (cluster.get('api') or {}).get('url')
    idps, err = OcmIdpModule.get_cluster_idps(api_instance, cluster_id)
    if err:
        return None, err

    cluster_admin = None
    for idp in idps:
        if idp.get('name') == 'cluster-admin':
            cluster_admin = idp
            break

    if not cluster_admin:
        return dict(
            exists=False,
            username=None,
            api_url=api_url,
            login_command=None,
            message="There is no 'cluster-admin' user on cluster '{}'.".format(cluster.get('name')),
        ), None

    username = 'cluster-admin'
    login_command = None
    if api_url:
        login_command = "oc login {} --username {}".format(api_url, username)

    return dict(
        exists=True,
        username=username,
        api_url=api_url,
        login_command=login_command,
        identity_provider=cluster_admin,
        message=(
            "There is 'cluster-admin' user on cluster '{}'. To login, run the following command:\n"
            "   {}".format(cluster.get('name'), login_command)
        ),
    ), None


def ocm_autoscaler_info_run(module):
    result = dict(autoscaler={})
    if module.check_mode:
        return result

    cluster_ref = module.params['cluster']
    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)
        cluster_id, cluster, err = resolve_cluster(api_instance, cluster_ref)
        if err:
            module.fail_json(msg=err)
        if not cluster_id:
            module.fail_json(msg="Unable to find cluster: {}".format(cluster_ref))
        autoscaler, err = fetch_autoscaler(api_instance, cluster_id)
        if err:
            module.fail_json(msg=err)
        result['autoscaler'] = autoscaler or {}
    return result


def ocm_machine_pool_info_run(module):
    result = dict(machine_pool={})
    if module.check_mode:
        return result

    cluster_ref = module.params['cluster']
    machine_pool = module.params['machine_pool']
    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)
        cluster_id, _, err = resolve_cluster(api_instance, cluster_ref)
        if err:
            module.fail_json(msg=err)
        if not cluster_id:
            module.fail_json(msg="Unable to find cluster: {}".format(cluster_ref))
        pool, err = fetch_machine_pool(api_instance, cluster_id, machine_pool)
        if err:
            module.fail_json(msg=err)
        if not pool:
            module.fail_json(
                msg="Machine pool '{}' not found on cluster '{}'".format(machine_pool, cluster_ref)
            )
        result['machine_pool'] = pool
    return result


def ocm_admin_info_run(module):
    result = dict(admin={})
    if module.check_mode:
        return result

    cluster_ref = module.params['cluster']
    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)
        cluster_id, cluster, err = resolve_cluster(api_instance, cluster_ref)
        if err:
            module.fail_json(msg=err)
        if not cluster_id:
            module.fail_json(msg="Unable to find cluster: {}".format(cluster_ref))
        admin, err = build_admin_info(api_instance, cluster_id, cluster)
        if err:
            module.fail_json(msg=err)
        result['admin'] = admin
    return result


def rosa_autoscaler_info_run(module):
    result = ocm_autoscaler_info_run(module)
    cluster = module.params['cluster']
    wrapped = dict(commands=[], autoscaler=result.get('autoscaler', {}))
    wrapped['commands'].append(_synthetic_command('autoscaler_info', cluster, wrapped['autoscaler']))
    return wrapped


def rosa_machine_pool_info_run(module):
    result = ocm_machine_pool_info_run(module)
    cluster = module.params['cluster']
    wrapped = dict(commands=[], machine_pool=result.get('machine_pool', {}))
    wrapped['commands'].append(
        _synthetic_command(
            'machine_pool_info',
            cluster,
            wrapped['machine_pool'],
        )
    )
    return wrapped


def rosa_admin_info_run(module):
    result = ocm_admin_info_run(module)
    cluster = module.params['cluster']
    wrapped = dict(commands=[], admin=result.get('admin', {}))
    wrapped['commands'].append(_synthetic_command('admin_info', cluster, wrapped['admin']))
    return wrapped


def fetch_upgrade_info(api_instance, cluster_id, cluster, machine_pool=None):
    cluster_name = cluster.get('name') or cluster_id
    hcp = bool((cluster.get('hypershift') or {}).get('enabled'))

    if machine_pool:
        try:
            http_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_node_pools_node_pool_id_upgrade_policies_get_without_preload_content(
                cluster_id,
                machine_pool,
                page=1,
                size=-1,
            )
            items, page = _list_page_from_response(http_response)
        except ApiException as e:
            if e.status == 404:
                items, page = [], {}
            else:
                return None, "Exception when calling node pool upgrade policies get: {}\n".format(e)

        message = (
            "No scheduled upgrades for machine pool '{}' in cluster '{}'".format(machine_pool, cluster_name)
            if not items
            else None
        )
        return dict(
            scope='machine_pool',
            machine_pool=machine_pool,
            items=items,
            page=page,
            message=message,
        ), None

    items = []
    page = {}
    if hcp:
        http_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_control_plane_upgrade_policies_get_without_preload_content(
            cluster_id,
            page=1,
            size=-1,
        )
        items, page = _list_page_from_response(http_response)
        source = 'control_plane_upgrade_policies'
    else:
        http_response = api_instance.api_clusters_mgmt_v1_clusters_cluster_id_upgrade_policies_get_without_preload_content(
            cluster_id,
            page=1,
            size=-1,
        )
        items, page = _list_page_from_response(http_response)
        source = 'upgrade_policies'

    message = (
        "No scheduled upgrades for cluster '{}'".format(cluster_name)
        if not items
        else None
    )
    return dict(
        scope='cluster',
        machine_pool=None,
        items=items,
        page=page,
        source=source,
        message=message,
    ), None


def ocm_upgrade_info_run(module):
    result = dict(upgrade={})
    if module.check_mode:
        return result

    cluster_ref = module.params['cluster']
    machine_pool = module.params.get('machine_pool')
    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)
        cluster_id, cluster, err = resolve_cluster(api_instance, cluster_ref)
        if err:
            module.fail_json(msg=err)
        if not cluster_id:
            module.fail_json(msg="Unable to find cluster: {}".format(cluster_ref))
        upgrade, err = fetch_upgrade_info(api_instance, cluster_id, cluster, machine_pool)
        if err:
            module.fail_json(msg=err)
        result['upgrade'] = upgrade
    return result


def rosa_upgrade_info_run(module):
    result = ocm_upgrade_info_run(module)
    cluster = module.params['cluster']
    machine_pool = module.params.get('machine_pool')
    wrapped = dict(commands=[], upgrade=result.get('upgrade', {}))
    wrapped['commands'].append(
        _synthetic_command('upgrade_info', cluster, wrapped['upgrade'], machine_pool=machine_pool)
    )
    return wrapped


def _synthetic_versions_command(payload, channel_group, hosted_cp, version_prefix=None):
    cmd = "ocm:list_versions(channel_group={}".format(channel_group)
    if hosted_cp:
        cmd += ",hosted_cp=true"
    if version_prefix:
        cmd += ",version={}".format(version_prefix)
    cmd += ")"
    return dict(
        command=cmd,
        rc=0,
        stdout=json.dumps(payload),
        stderr='',
    )


def _version_search(channel_group, hosted_cp, version_prefix=None):
    search = "enabled = true AND channel_group = '{}'".format(
        _escape_ocm_search_literal(channel_group)
    )
    if hosted_cp:
        search += " AND hosted_control_plane_enabled = true"
    else:
        search += " AND rosa_enabled = true"
    if version_prefix:
        search += " AND raw_id like '{}%'".format(_escape_ocm_search_literal(version_prefix))
    return search


def _normalize_version_record(item):
    record = dict(item)
    record['version'] = item.get('raw_id')
    record['default_display'] = 'yes' if item.get('default') else 'no'
    upgrades = item.get('available_upgrades') or []
    if upgrades and not isinstance(upgrades[0], str):
        upgrades = [u.get('raw_id', u) if isinstance(u, dict) else str(u) for u in upgrades]
    record['available_upgrades'] = upgrades
    record['available_upgrades_display'] = ', '.join(upgrades) if upgrades else ''
    return record


def fetch_versions(api_instance, channel_group, hosted_cp, version_prefix=None):
    search = _version_search(channel_group, hosted_cp, version_prefix)
    http_response = api_instance.api_clusters_mgmt_v1_versions_get_without_preload_content(
        page=1,
        size=-1,
        order='default desc, id desc',
        search=search,
    )
    payload = _decode_ocm_http_response(http_response)
    if _is_error_payload(payload):
        return None, "OCM versions error: {}".format(payload.get('reason', payload))
    items = payload.get('items') or []
    return [_normalize_version_record(item) for item in items], None


def ocm_version_info_run(module):
    result = dict(versions=[])
    if module.check_mode:
        return result

    channel_group = module.params.get('channel_group') or 'stable'
    hosted_cp = bool(module.params.get('hosted_cp'))
    version_prefix = module.params.get('version')

    with ocm_client.ApiClient(OcmModule.ocm_authenticate()) as api_client:
        api_instance = ocm_client.DefaultApi(api_client)
        versions, err = fetch_versions(
            api_instance,
            channel_group,
            hosted_cp,
            version_prefix,
        )
        if err:
            module.fail_json(msg=err)
        result['versions'] = versions
    return result


def rosa_versions_info_run(module):
    result = ocm_version_info_run(module)
    channel_group = module.params.get('channel_group') or 'stable'
    hosted_cp = bool(module.params.get('hosted_cp'))
    version_prefix = module.params.get('version')
    wrapped = dict(commands=[], versions=result.get('versions', []))
    wrapped['commands'].append(
        _synthetic_versions_command(
            wrapped['versions'],
            channel_group,
            hosted_cp,
            version_prefix,
        )
    )
    return wrapped
