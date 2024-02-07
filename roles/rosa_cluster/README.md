rosa_cluster
=========

The rosa_cluster role will create or destroy a ROSA cluster

Requirements
------------

Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

Role Variables
--------------

```yaml
state: present|absent
rosa_cluster:
  name: rosa-cluster
  admin_username: admin
  admin_password: 'MyRosa1234!'
  subnet_ids: []
  http_proxy: http://{{ proxy_private_ip }}:3128
  https_proxy: http://{{ proxy_private_ip }}:3128
  no_proxy: ~
  additional_trust_bundle_file: "roles/proxy_create/files/squid-ca-cert.pem"
  disable_workload_monitoring: false
  aws_account_id: ~
  account_roles_prefix: Managed-OpenShift
  region: us-east-2
  private_link: false
  vpc_cidr: 10.0.0.0/20
  multi_az: false
  version: 4.14
  hosted_cp: false
  autoscaling: false
  min_replicas:
  max_replicas:
  compute_nodes: # 3 for multi-az, 2 for single-az
  compute_machine_type: "m5.xlarge"
  role_arn:
  support_role_arn:
  controlplane_iam_role:
  worker_iam_role:
  operator_roles_prefix:
  kms_key_arn:
  tags: {}
  wait: true
```

License
-------

Copyright 2024 Red Hat

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


