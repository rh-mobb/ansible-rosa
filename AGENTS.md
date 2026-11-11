# AI agent guide — ansible-rosa

Guidance for coding agents working in this repository. Humans should treat [README.md](README.md) as the primary user-facing doc; this file is for architecture, conventions, and safe automation.

## What this repo is

- **Project**: Community Ansible automation for **ROSA on AWS** (Classic and Hosted Control Plane / HCP).
- **Galaxy collection**: `rh_mobb.rosa` (see [galaxy.yml](galaxy.yml); published on tag via [.github/workflows/release.yaml](.github/workflows/release.yaml)).
- **Upstream**: [github.com/rh-mobb/ansible-rosa](https://github.com/rh-mobb/ansible-rosa) — MOBB OSS support, not an official Red Hat product.
- **Not in scope**: Azure ARO, GCP OSD, or the Terraform-based [vp-terraform-rosa](https://github.com/rh-mobb/vp-terraform-rosa) validated pattern. Cross-reference those only when the user explicitly compares approaches.

## High-level layout

```
ansible-rosa/
├── ansible.cfg              # default inventory, plugin paths, hash_behaviour=merge
├── galaxy.yml               # collection metadata and version
├── requirements.txt         # Python deps (ansible-core, ocm-python, boto3, lint)
├── requirements.yml         # Ansible Galaxy collections (amazon.aws, kubernetes.core, …)
├── Makefile                 # virtualenv, create/delete per environment, galaxy build
├── create-cluster.yaml      # primary provision playbook (state: present)
├── delete-cluster.yaml      # teardown playbook (state: absent)
├── install.yml / uninstall.yml  # alternate HCP-oriented playbooks (legacy path)
├── environment/<name>/      # example inventories (group_vars/all.yaml, hosts)
├── plugins/
│   ├── modules/             # custom modules (rosa_cluster, ocm_*, ec2_*)
│   └── module_utils/        # shared Python (e.g. ocm.py)
├── roles/                   # active roles (present/absent task pattern)
│   └── _archive/            # deprecated roles — do not extend
├── docs/                    # module docs and architecture images
└── staging/                 # runtime scratch (created by playbooks)
```

### Example environments (`environment/`)

| Directory | Makefile target | Scenario |
|-----------|-----------------|----------|
| `default` | `make create` / `delete` | Single-AZ BYO VPC, public Classic STS |
| `multi-az` | `make create.multiaz` | Multi-AZ Classic |
| `private-link` | `make create.pl` / `create.private` | PrivateLink Classic (+ optional BYOK via `rosa_kms_key_arn`) |
| `transit-gateway-egress` | `make create.tgw` | PrivateLink + TGW + egress VPC, Squid proxy, jumphost, DNS forwarder |
| `hcp` | `make create.hcp` | ROSA HCP |
| `cicd-demo` | (inventory only) | CI/demo variables |

Cluster naming defaults to `ans-<username>` via `CLUSTER_NAME` in the Makefile. Account role prefix is tied to `cluster_name` (HCP uses a `-HCP-ROSA` suffix).

## How provisioning works

1. **Playbook init** (`create-cluster.yaml` / `delete-cluster.yaml`): sets global `state` (`present` | `absent`), `ansible_python_interpreter` to `./virtualenv/bin/python`, and `aws_account_id` via `aws_caller_info`.
2. **Role chain** (order matters): `_vars` → `network_math` → optional `rosa_transit_gateway`, `rosa_egress_vpc`, `rosa_vpc`, `rosa_ec2_instance` (jumphost/proxy) → `rosa_account_roles` → `rosa_cluster` → optional `rosa_dns_resolver` → `finish`.
3. **Per-role API**: each infrastructure role expects a **single nested dict** named after the role (e.g. `rosa_cluster: { name, region, hosted_cp, … }`) plus top-level `state`.
4. **Conditionals** in the playbook gate optional networking (TGW, egress, proxy, DNS) on inventory variables such as `rosa_tgw_enabled`, `rosa_private_link`, `proxy_enabled`.

Agents editing the playbook should preserve role order on delete (reverse dependency logic lives inside roles, but playbook structure must stay symmetric between create and delete).

## Active roles (use these)

| Role | Purpose |
|------|---------|
| `_vars` | Shared defaults across MOBB ROSA roles |
| `network_math` | CIDR / subnet calculations |
| `rosa_vpc` | ROSA workload VPC |
| `rosa_egress_vpc` | Egress VPC for PrivateLink / TGW patterns |
| `rosa_transit_gateway` | AWS Transit Gateway attachment |
| `rosa_ec2_instance` | Jumphost and Squid proxy instances |
| `rosa_account_roles` | STS account roles (Classic vs HCP templates under `files/`) |
| `rosa_operator_roles` | Operator IAM roles |
| `rosa_cluster` | Cluster create/delete (wraps modules + ROSA CLI) |
| `rosa_dns_resolver` | Route53 resolver rules for TGW topologies |
| `kms_create` | BYOK / KMS helpers |
| `service_quotas` | AWS quota checks |
| `finish` | End-of-playbook housekeeping |

Each role’s variable schema is documented in its `README.md`. Prefer updating that README when you change the public variable contract.

**`roles/_archive/`** holds superseded implementations. Do not copy from `_archive` into new code; migrate patterns into the active roles above.

## Custom Ansible modules

Modules live under [plugins/modules/](plugins/modules/) and are loaded via [ansible.cfg](ansible.cfg) `library` paths.

| Module | Typical use |
|--------|-------------|
| `rosa_cluster` / `rosa_cluster_info` | Legacy module names and return keys; delegate to OCM via [module_utils/ocm_cluster_lib.py](plugins/module_utils/ocm_cluster_lib.py) |
| `rosa_admin_info` / `rosa_autoscaler_info` / `rosa_machine_pool_info` / `rosa_upgrade_info` / `rosa_versions_info` | Legacy ``rosa describe/list`` return keys; delegate via [module_utils/ocm_info_lib.py](plugins/module_utils/ocm_info_lib.py) |
| `ocm_cluster` / `ocm_cluster_info` / `ocm_version_info` | OCM API via [rh-mobb/ocm-python](https://github.com/rh-mobb/ocm-python) |
| `ocm_admin_info` / `ocm_autoscaler_info` / `ocm_machine_pool_info` / `ocm_upgrade_info` | OCM cluster sub-resource lookups (same lib as rosa info wrappers) |
| `ocm_oidc_config` / `oidc_provider` / `ocm_idp` | OIDC / IdP configuration |
| `ec2_transit_gateway` / `transit_gateway_route` | TGW resources |
| `route53_zone` | DNS zones |
| `peer_cert_chain_info` | TLS chain inspection |

Module documentation belongs in each file’s `DOCUMENTATION` block; [docs/modules.md](docs/modules.md) is a partial mirror — update both when changing user-facing options.

Python module style in this repo: GPL-3.0+ header, `AnsibleModule` pattern, ROSA CLI or OCM SDK invocation in module code, idempotent `present`/`absent` where feasible.

## Prerequisites (for humans and agents running playbooks)

- **Python 3.11+** on the control node (`make virtualenv` enforces this).
- AWS account with ROSA enabled, AWS CLI configured.
- ROSA CLI (`rosa login` or token via env / Ansible vars).
- `make virtualenv` before any local `ansible-playbook` (installs deps and Galaxy collections).
- Optional: `IGNORE_CERTS=true make virtualenv` only when Galaxy TLS issues are understood and accepted.

**Authentication paths**: pre-login (`aws configure`, `rosa login`) or Ansible-driven credentials via inventory/extra vars (see README).

## Safety rules for agents

1. **Do not run `make create*` or `ansible-playbook create-cluster.yaml` unless the user explicitly asks** — this provisions paid AWS/ROSA infrastructure.
2. **Do not run `make delete*` without explicit confirmation** — destructive across VPCs, IAM roles, and clusters.
3. **Never commit secrets** — tokens, `ROSA_TOKEN`, AWS keys, KMS ARNs, or contents of `~/.aws` / `~/.ocm.json`.
4. **Avoid regenerating Squid TLS material** (`make squid.certs`) unless the user requests it; committed certs under `roles/rosa_ec2_instance/files/` are part of the PrivateLink proxy workflow.
5. **Default inventory** in `ansible.cfg` is `environment/default`; always pass `-i` explicitly when targeting another environment (Makefile does this correctly).
6. **Pin or document ROSA/OpenShift versions** when changing defaults in `group_vars/all.yaml` — clusters may fail if a version leaves support.

## Local development workflow

```bash
make virtualenv

# Lint (after venv exists)
./virtualenv/bin/ansible-lint create-cluster.yaml delete-cluster.yaml

# Build collection artifact (does not publish)
make galaxy.build
```

- **Ansible version**: pinned in [requirements.txt](requirements.txt) (`ansible==10.x` line).
- **Collections**: [requirements.yml](requirements.yml) — use FQCN in new tasks (`amazon.aws.ec2_vpc`, `ansible.builtin.set_fact`, etc.) when touching playbooks.
- **Hash merge**: `hash_behaviour = merge` in `ansible.cfg` — nested dicts in group_vars combine with role defaults; test merged results when adding keys.

### Podman workflow

Use **Podman** (not Docker) for container builds and runs: `make image` (`podman build`), `make podman.create` / `make podman.delete`. Volume mounts use the `:Z` relabel suffix for SELinux hosts. Images use **Fedora 41** ([Dockerfile](Dockerfile)) or **UBI 9 + Python 3.11** ([Dockerfile.ubi](Dockerfile.ubi)) so the venv matches ocm-python 0.4.0. ROSA/AWS CLI versions in those container recipes may lag local CLIs — note drift when debugging module vs CLI behavior.

## Configuration conventions

- **Inventory variables** live in `environment/<env>/group_vars/all.yaml` (cluster name, region, CIDRs, feature flags).
- **Cross-playbook vars** may appear in [vars/main.yaml](vars/main.yaml); init playbooks set facts that roles consume.
- **Extra tags** for cost/accountability: `extra_tags` map in group vars (propagated to AWS resources).
- **Classic vs HCP**: `rosa_hosted_cp` drives account/operator role templates and cluster module options — verify both code paths when changing IAM JSON under `roles/rosa_account_roles/files/` or `roles/rosa_operator_roles/`.

## Releases

1. Bump `version` in [galaxy.yml](galaxy.yml) and record changes in [CHANGELOG.md](CHANGELOG.md).
2. Tag the commit (tag name becomes Galaxy version in CI).
3. Push tag → GitHub Action publishes to Ansible Galaxy with `ANSIBLE_GALAXY_API_TOKEN`.

Collection `dependencies` in `galaxy.yml` pull in `amazon.aws` and `community.aws` for consumers. `build_ignore` excludes `.history` and `*.py.old`. `meta/runtime.yml` sets `requires_ansible: '>=2.17.0'`.

Local publish: `make galaxy.build` then `make galaxy.publish` (requires `ANSIBLE_GALAXY_API_KEY`).

## Making changes — agent checklist

| Change type | Touch |
|-------------|--------|
| New cluster option | `roles/rosa_cluster`, module `rosa_cluster.py`, playbook vars, relevant `environment/*/group_vars` example |
| Networking / TGW | `rosa_vpc`, `rosa_egress_vpc`, `rosa_transit_gateway`, `network_math` |
| IAM policy JSON | Versioned paths under `rosa_account_roles/files/{classic,hcp}/<version>/` |
| New example topology | New `environment/<name>/` + Makefile targets mirroring existing patterns |
| Collection metadata | `galaxy.yml`, README if user-facing |

Keep diffs minimal; match existing YAML style and the `present/main.yml` + `absent/main.yml` split in roles.

## Debugging playbook failures

1. **Confirm context**: environment inventory, `cluster_name`, `rosa_account_roles_prefix`, and `state`.
2. **Verify tooling**: `./virtualenv/bin/python`, `rosa`, `aws sts get-caller-identity`, `rosa whoami`.
3. **Re-run with verbosity**: `make create VERBOSITY=-vvvv` or `EXTRA_VARS='…'`.
4. **Inspect staged data**: `staging/` under repo root after failed runs.
5. **Separate layers**: AWS API errors (VPC/IAM) vs OCM/ROSA errors (cluster state) vs proxy/DNS (PrivateLink/TGW only).
6. **Module vs role**: roles orchestrate; modules implement API/CLI — fix at the lowest layer that matches the failure.

For OCM-specific API behavior, compare with [ocm-python](https://github.com/rh-mobb/ocm-python) version pinned in `requirements.txt`.

**ocm-python 0.4.0:** some list/get responses (clusters, identity providers) do not deserialize cleanly with generated Pydantic models when OCM returns link-shaped nested fields. `plugins/module_utils/ocm.py` uses `*_without_preload_content` and JSON parsing for those reads; request bodies still use typed models where appropriate.

## Related skills and repos

When users need CLI syntax or product behavior not defined in this tree:

- ROSA CLI: MOBB `rosa-cli` skill (Classic vs HCP differences matter).
- OCM API: MOBB `ocm-cli` skill.
- Terraform-first HCP patterns: `vp-terraform-rosa` workspace.

## Git and commits

- Create commits or PRs only when the user asks.
- Do not push or publish to Galaxy without explicit request.
- Issue tracking is informal (README “ToDos”); prefer GitHub issues on `rh-mobb/ansible-rosa` for new backlog items if the user wants tracking.

## Summary for quick orientation

**ansible-rosa** = Ansible Galaxy collection + example playbooks that provision ROSA on AWS using composable roles, custom modules, and environment-specific inventories. **Create** and **delete** are driven by global `state` and Makefile-selected inventories. Treat infrastructure commands as production-affecting; prefer lint, small role-scoped changes, and README/module docs updates alongside code.
