rosa_ec2_instance
=========

A helper role to create ec2 instances that can be used as jumphosts or secure proxies for ROSA clusters to more easily allow for access to the private ROSA cluster from a local machine.


Role Variables
--------------

```yaml
state: present|absent
rosa_ec2_instance:
  name: rosa-ec2-instance
  ami: "" # if left blank will pick latest RHEL 8 AMI based on the below pattern
  ami_name: "RHEL-8.*_HVM-*-x86_64-*Hourly*"
  ami_owner: "309956199498"
  instance_type: t2.micro
  region: us-east-2
  user_data: # "{{ lookup('file', 'basic_user_data.sh') }}"
  user_data_template: ~
  assign_public_ip: false
  vpc_id:
  subnet_id:
  security_group_rules:
    - proto: tcp
      ports: [22]
      cidr_ip: 0.0.0.0/0
      rule_desc: allow ssh
  ssh_public_key: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
  tags: {}
  # extra vars that can be set for templates
  template_vars: {}

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


