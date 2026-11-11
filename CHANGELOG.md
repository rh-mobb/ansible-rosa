# Changelog

All notable changes to the `rh_mobb.rosa` collection are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [4.1.0] - 2026-11-11

### Added

- `ocm_machine_pools_info` and `rosa_machine_pools_info` for ``rosa list machinepool`` (OCM machine pool / HCP node pool list). Singular modules remain ``rosa describe machinepool``.

## [4.0.0] - 2026-11-11

### Added

- OCM-backed info modules: `ocm_admin_info`, `ocm_autoscaler_info`, `ocm_machine_pool_info`, `ocm_upgrade_info`, `ocm_version_info`.
- Legacy ROSA-shaped wrappers: `rosa_admin_info`, `rosa_autoscaler_info`, `rosa_machine_pool_info`, `rosa_upgrade_info`, `rosa_versions_info`.
- Shared libraries `ocm_cluster_lib.py` and `ocm_info_lib.py`.
- Module reference: [docs/modules.md](docs/modules.md).
- [AGENTS.md](AGENTS.md) for contributor and agent guidance.

### Changed

- **BREAKING:** `rosa_cluster`, `rosa_cluster_info`, and cluster create/delete paths use the OCM API (via shared libs), not the ROSA CLI; behavior and return shapes follow OCM, not CLI exit codes.
- **BREAKING:** Minimum **ansible-core 2.17** (`requires_ansible: '>=2.17.0'`), control node **Python 3.11+**, and **ocm-python 0.4.0** (see `requirements.txt`).
- Podman-based container workflow; Fedora 41 / UBI 9 images.
- Collection declares Galaxy dependencies on `amazon.aws` and `community.aws` (>= 6.0.0).
- Documented Galaxy install path and Python deps in README.

### Removed

- Obsolete `plugins/modules/ec2_vpc_route_table.py.old`.

### Fixed

- `ocm_idp` and `ocm_oidc_config` documentation (removed invalid doc fragments; corrected FQCN examples).
- `ocm_oidc_config` RETURN block for `ansible-doc` compatibility.

### Packaging

- `build_ignore` excludes `.history`, `**/*.py.old`, and local artifacts.

## [3.0.3] and earlier

See Git history and release tags on [GitHub](https://github.com/rh-mobb/ansible-rosa/releases).
