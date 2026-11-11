# Ansible ROSA modules (`rh_mobb.rosa`)

Collection modules live under `plugins/modules/`. Each file’s `DOCUMENTATION` block is authoritative; this page is a human-readable index and mirror.

**FQCN:** `rh_mobb.rosa.<module_name>` (for example `rh_mobb.rosa.ocm_cluster`).

**Authentication:** OCM modules use OCM API credentials (typically from `rosa login` / `~/.ocm.json` or `OCM_TOKEN`). AWS modules use normal boto3 credentials. Run playbooks with `ansible_python_interpreter` pointing at the repo virtualenv after `make virtualenv` (Python 3.11+, [ocm-python](https://github.com/rh-mobb/ocm-python) 0.4.0).

**OCM vs `rosa_*` wrappers:** Pairs such as `ocm_cluster_info` and `rosa_cluster_info` call the same libraries. `rosa_*` modules keep legacy return keys (`commands`, `details` / `cluster`, table-friendly version fields, and so on). New playbooks should prefer `ocm_*` unless you need ROSA CLI-shaped output.

**Full option lists:** After `make virtualenv`:

```bash
./virtualenv/bin/ansible-doc rh_mobb.rosa.<module_name>
```

---

## Module index

| Module | Summary | ROSA CLI / notes |
|--------|---------|------------------|
| [ocm_cluster](#ocm_cluster--rosa_cluster) | Create, delete, dry-run ROSA via OCM | `rosa create/delete cluster` (API-backed) |
| [rosa_cluster](#ocm_cluster--rosa_cluster) | Same; legacy `commands` / `details` | Same |
| [ocm_cluster_info](#ocm_cluster_info--rosa_cluster_info) | Get cluster by name | `rosa describe cluster` |
| [rosa_cluster_info](#ocm_cluster_info--rosa_cluster_info) | Same + `commands` | Same |
| [ocm_version_info](#ocm_version_info--rosa_versions_info) | Installable OpenShift versions | `rosa list versions` |
| [rosa_versions_info](#ocm_version_info--rosa_versions_info) | Same + `default_display`, `commands` | Same |
| [ocm_admin_info](#cluster-info-pairs) | cluster-admin IdP / login hints | `rosa describe admin` |
| [rosa_admin_info](#cluster-info-pairs) | Same + `commands` | Same |
| [ocm_autoscaler_info](#cluster-info-pairs) | Cluster autoscaler | `rosa describe autoscaler` |
| [rosa_autoscaler_info](#cluster-info-pairs) | Same + `commands` | Same |
| [ocm_machine_pools_info](#cluster-info-pairs) | All machine or node pools | `rosa list machinepool` |
| [rosa_machine_pools_info](#cluster-info-pairs) | Same + `commands` | Same |
| [ocm_machine_pool_info](#cluster-info-pairs) | One machine pool or HCP node pool | `rosa describe machinepool` |
| [rosa_machine_pool_info](#cluster-info-pairs) | Same + `commands` | Same |
| [ocm_upgrade_info](#cluster-info-pairs) | Scheduled upgrade policies | `rosa describe upgrade` |
| [rosa_upgrade_info](#cluster-info-pairs) | Same + `commands` | Not `rosa list upgrades` |
| [ocm_oidc_config](#ocm_oidc_config) | Managed OIDC configs for STS/HCP | OCM OIDC configs |
| [ocm_idp](#ocm_idp) | Cluster identity providers | `rosa create idp` (htpasswd) |
| [oidc_provider](#oidc_provider) | IAM OIDC provider | AWS IAM |
| [ec2_transit_gateway](#ec2_transit_gateway) | Transit Gateway lifecycle | AWS EC2 |
| [transit_gateway_route](#transit_gateway_route) | TGW route table entries | AWS EC2 |
| [route53_zone](#route53_zone) | Route53 public/private zones | AWS Route53 |
| [peer_cert_chain_info](#peer_cert_chain_info) | TLS peer chain + thumbprint | Proxy / OIDC thumbprints |

---

## Cluster lifecycle

### `ocm_cluster` / `rosa_cluster`

Create, update-oriented presence, delete, or dry-run a ROSA cluster through the OCM API (`plugins/module_utils/ocm_cluster_lib.py`).

| Option | Required | Notes |
|--------|----------|-------|
| `name` | yes | Cluster name |
| `state` | no | `present` (default), `absent`, `dry-run`, `describe` (`rosa_cluster` only for `describe`) |
| `region`, `version`, `channel_group` | no | Region and install version |
| `multi_az`, `private`, `private_link`, `hosted_cp` | no | Topology flags |
| `subnet_ids`, CIDRs (`machine_cidr`, `service_cidr`, `pod_cidr`, `host_prefix`) | no | BYO VPC networking |
| `compute_machine_type`, `compute_nodes`, `enable_autoscaling`, `min_replicas`, `max_replicas` | no | Workers |
| `sts`, `aws_account_id`, IAM role ARNs, `operator_roles_prefix`, `oidc_config_id` | no | STS / HCP IAM |
| `http_proxy`, `https_proxy`, `no_proxy`, `additional_trust_bundle_file` | no | Proxy |
| `wait` | no | Wait for create/delete to finish |

**Returns:** `ocm_cluster` — cluster fields from OCM. `rosa_cluster` — `commands`, `details` (and related legacy keys).

**Example:**

```yaml
- name: Ensure ROSA cluster exists
  rh_mobb.rosa.ocm_cluster:
    name: my-cluster
    region: us-east-1
    version: "4.14.17"
    sts: true
    subnet_ids: "subnet-a,subnet-b,subnet-c,subnet-d"
    state: present
```

---

### `ocm_cluster_info` / `rosa_cluster_info`

| Option | Required |
|--------|----------|
| `name` | yes |

**Returns:** `cluster` (OCM object). `rosa_cluster_info` also returns `commands`.

```yaml
- rh_mobb.rosa.ocm_cluster_info:
    name: my-cluster
  register: cluster_info
```

---

## Versions catalog

### `ocm_version_info` / `rosa_versions_info`

Lists enabled install images from OCM (same filters as `rosa list versions`).

| Option | Default | Notes |
|--------|---------|-------|
| `channel_group` | `stable` | ROSA `--channel-group` |
| `hosted_cp` | `false` | When true, only HCP-enabled versions (`--hosted-cp`) |
| `version` | — | Prefix filter on `raw_id` (for example `4.22`) |

**Returns:** `versions` — each item includes `version` (`raw_id`), `default`, `available_upgrades`. `rosa_versions_info` adds `default_display`, `available_upgrades_display`, and `commands`.

Used by `roles/rosa_cluster` (`ocm_version_info`) to pick a default image when `version` is not pinned.

```yaml
- rh_mobb.rosa.rosa_versions_info:
    hosted_cp: true
    version: "4.22"
  register: versions
```

`rosa list upgrades -c <cluster>` is a different operation; use [upgrade info modules](#cluster-info-pairs) for scheduled policies on a cluster.

---

## Cluster info pairs

Shared behavior: `cluster` (name or ID) is required unless noted. Implementation: `plugins/module_utils/ocm_info_lib.py`.

### `ocm_admin_info` / `rosa_admin_info`

| Option | Required |
|--------|----------|
| `cluster` | yes |

**Returns:** `admin` (IdP presence, API URL, suggested `oc login`). `rosa_admin_info` adds `commands`.

### `ocm_autoscaler_info` / `rosa_autoscaler_info`

| Option | Required |
|--------|----------|
| `cluster` | yes |

**Returns:** `autoscaler` (+ `commands` on rosa wrapper).

### `ocm_machine_pools_info` / `rosa_machine_pools_info`

| Option | Required |
|--------|----------|
| `cluster` | yes |

Lists all pools on the cluster (classic `machine_pools`, HCP `node_pools`).

**Returns:** `machine_pools` (+ `commands` on rosa wrapper).

```yaml
- rh_mobb.rosa.ocm_machine_pools_info:
    cluster: my-cluster
  register: pools
```

### `ocm_machine_pool_info` / `rosa_machine_pool_info`

| Option | Required |
|--------|----------|
| `cluster` | yes |
| `machine_pool` | yes | Pool ID (for example `workers`) |

Classic clusters use machine pools; HCP uses node pools with the same API shape.

**Returns:** `machine_pool` (+ `commands` on rosa wrapper).

### `ocm_upgrade_info` / `rosa_upgrade_info`

| Option | Required |
|--------|----------|
| `cluster` | yes |
| `machine_pool` | no | Pool-specific scheduled upgrades (`--machinepool`) |

**Returns:** `upgrade` (scheduled policies; HCP control plane vs node pool paths handled in the library).

```yaml
- rh_mobb.rosa.ocm_upgrade_info:
    cluster: my-cluster
    machine_pool: workers
```

---

## OCM identity

### `ocm_oidc_config`

Manage OCM OIDC configurations for unmanaged STS / HCP installs.

| Option | Required | Notes |
|--------|----------|-------|
| `state` | yes | `present` (pick unused or create), `absent` |
| `id` | no | Config ID (for delete) |

**Returns:** `oidc_config` (id, issuer_url, managed, installer_role_arn, and related fields).

### `ocm_idp`

Manage cluster identity providers (htpasswd supported).

| Option | Required | Notes |
|--------|----------|-------|
| `name` | yes | IdP name |
| `type` | yes | Currently `htpasswd` |
| `cluster_name` or `cluster_id` | one of | Target cluster |
| `username`, `password` | no | htpasswd user |

**Returns:** IdP metadata per module `RETURN`.

---

## AWS helpers (PrivateLink / TGW playbooks)

### `oidc_provider`

IAM OpenID Connect provider for ROSA STS trust.

| Option | Required |
|--------|----------|
| `url` | yes |
| `thumbprints` | yes |
| `state` | yes (`present` / `absent`) |
| `client_ids`, `tags` | no |

### `ec2_transit_gateway`

Create, tag, or delete a Transit Gateway (ASN, DNS support, auto-attach/associate/propagate, tags, `state`).

### `transit_gateway_route`

| Option | Required |
|--------|----------|
| `destination_cidr_block` | yes |
| `region` | yes |
| `transit_gateway_route_table_id` | yes |
| `transit_gateway_attachment_id` | yes |
| `state` | yes |
| `blackhole`, `tags` | no |

### `route53_zone`

Create or delete public or private Route53 zones (`zone`, `state`, `vpc_id` / `vpcs`, tags, comment). Forked from community.aws patterns for playbook use.

### `peer_cert_chain_info`

Fetch TLS certificate chain from a host (used for proxy trust / OIDC thumbprint discovery).

| Option | Required |
|--------|----------|
| `host` | yes |
| `port` | no (default 443) |

**Returns:** `chain`, `ca_cert`, `ca_thumbprint`.

---

## Maintaining this document

When you add or change module options or return values:

1. Update the module’s `DOCUMENTATION` / `EXAMPLES` / `RETURN` in `plugins/modules/`.
2. Update the matching section (or table row) in this file.
3. For architecture notes, see [AGENTS.md](../AGENTS.md).
