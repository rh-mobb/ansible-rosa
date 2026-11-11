.DEFAULT_GOAL := help
.PHONY: help virtualenv kind image deploy

VERBOSITY ?= "-vvv"

CLUSTER_NAME ?= ans-$(shell whoami)

VIRTUALENV ?= "./virtualenv/"
ANSIBLE = $(VIRTUALENV)/bin/ansible-playbook $(VERBOSITY) $(EXTRA_VARS)

IGNORE_CERTS ?= false
IGNORE_CERTS_OPTION=
ifeq ($(IGNORE_CERTS), true)
IGNORE_CERTS_OPTION = --ignore-certs
endif

help:
	@echo GLHF

virtualenv:
		@python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
			|| (echo "Python 3.11+ required (ocm-python 0.4.0)" && exit 1)
		LC_ALL=en_US.UTF-8 python3 -m venv $(VIRTUALENV)
		. $(VIRTUALENV)/bin/activate
		$(VIRTUALENV)/bin/pip install pip --upgrade
		LC_ALL=en_US.UTF-8 $(VIRTUALENV)/bin/pip3 install -r requirements.txt #--use-feature=2020-resolver
		$(VIRTUALENV)/bin/ansible-galaxy collection install -r requirements.yml $(IGNORE_CERTS_OPTION)

podman.image:
	podman build -t quay.io/pczar/ansible-rosa .

podman.image.push:
	podman push quay.io/pczar/ansible-rosa

podman.image.pull:
	podman pull quay.io/pczar/ansible-rosa

# podman shortcuts
build: podman.image
image: podman.image
push: podman.image.push
pull: podman.image.pull


create:
	$(ANSIBLE) create-cluster.yaml -i ./environment/default/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)"

delete:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/default/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)"

create.multiaz:
	$(ANSIBLE) create-cluster.yaml -i ./environment/multi-az/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)"

create.private:
	$(ANSIBLE) create-cluster.yaml -i ./environment/private-link/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)"

delete.private:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/private-link/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)"

create.pl: create.private

delete.pl: delete.private


delete.multiaz:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/multi-az/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)"

create.tgw:
	$(ANSIBLE) create-cluster.yaml -i ./environment/transit-gateway-egress/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)"

delete.tgw:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/transit-gateway-egress/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)"

create.hcp:
	$(ANSIBLE) create-cluster.yaml -i ./environment/hcp/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)-HCP-ROSA"

delete.hcp:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/hcp/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)-HCP-ROSA"

create.new:
	$(ANSIBLE) install.yml -i ./environment/hcp/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)-HCP-ROSA"
delete.new:
	$(ANSIBLE) uninstall.yml -i ./environment/hcp/hosts \
	  --extra-vars "cluster_name=$(CLUSTER_NAME) rosa_account_roles_prefix=$(CLUSTER_NAME)-HCP-ROSA"

podman.create: image
	podman run --rm \
		-v $(HOME)/.ocm.json:/home/ansible/.ocm.json:Z \
		-v $(HOME)/.aws:/home/ansible/.aws:Z \
	  -ti quay.io/pczar/ansible-rosa \
		$(ANSIBLE) -v create-cluster.yaml

podman.delete: image
	podman run --rm \
		-v $(HOME)/.ocm.json:/home/ansible/.ocm.json:Z \
		-v $(HOME)/.aws:/home/ansible/.aws:Z \
	  -ti quay.io/pczar/ansible-rosa \
		$(ANSIBLE) -v delete-cluster.yaml


galaxy.build:
	ansible-galaxy collection build --force .

galaxy.publish:
	VERSION=$$(yq e '.version' galaxy.yml); \
	ansible-galaxy collection publish rh_mobb-rosa-$$VERSION.tar.gz --api-key=$$ANSIBLE_GALAXY_API_KEY

squid.certs:
	openssl req -new -newkey rsa:2048 -sha256 -days 365 \
	  -subj '/C=US/CN=squid.proxy' \
	  -nodes -x509 -extensions v3_ca -keyout roles/rosa_ec2_instance/files/squid-ca-key.pem \
		-out roles/rosa_ec2_instance/files/squid-ca-cert.pem
	cat roles/rosa_ec2_instance/files/squid-ca-cert.pem \
	    roles/rosa_ec2_instance/files/squid-ca-key.pem \
			> roles/rosa_ec2_instance/files/squid-ca-cert-key.pem
