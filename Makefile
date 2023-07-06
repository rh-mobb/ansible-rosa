.DEFAULT_GOAL := help
.PHONY: help virtualenv kind image deploy


CLUSTER_NAME ?= ans-$(shell whoami)
EXTRA_VARS ?= --extra-vars "cluster_name=$(CLUSTER_NAME)"

VIRTUALENV ?= "./virtualenv/"
ANSIBLE = $(VIRTUALENV)/bin/ansible-playbook -v $(EXTRA_VARS)


help:
	@echo GLHF

virtualenv:
		LC_ALL=en_US.UTF-8 python3 -m venv $(VIRTUALENV)
		. $(VIRTUALENV)/bin/activate
		pip install pip --upgrade
		LC_ALL=en_US.UTF-8 $(VIRTUALENV)/bin/pip3 install -r requirements.txt #--use-feature=2020-resolver
		$(VIRTUALENV)/bin/ansible-galaxy collection install -r requirements.yml

docker.image:
	docker build -t quay.io/pczar/ansible-rosa .

docker.image.push:
	docker push quay.io/pczar/ansible-rosa

docker.image.pull:
	docker pull quay.io/pczar/ansible-rosa

# docker shortcuts
build: docker.image
image: docker.image
push: docker.image.push
pull: docker.image.pull


create:
	$(ANSIBLE) create-cluster.yaml

delete:
	$(ANSIBLE) delete-cluster.yaml

create.multiaz:
	$(ANSIBLE) create-cluster.yaml -i ./environment/multi-az/hosts

create.private:
	$(ANSIBLE) create-cluster.yaml -i ./environment/private-link/hosts

delete.private:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/private-link/hosts

delete.multiaz:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/multi-az/hosts

create.tgw:
	$(ANSIBLE) create-cluster.yaml -i ./environment/transit-gateway-egress/hosts

delete.tgw:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/transit-gateway-egress/hosts

create.hcp:
	$(ANSIBLE) create-cluster.yaml -i ./environment/hcp/hosts

delete.hcp:
	$(ANSIBLE) delete-cluster.yaml -i ./environment/hcp/hosts


docker.create: image
	docker run --rm \
		-v $(HOME)/.ocm.json:/home/ansible/.ocm.json \
		-v $(HOME)/.aws:/home/ansible/.aws \
	  -ti quay.io/pczar/ansible-rosa \
		$(ANSIBLE) -v create-cluster.yaml

docker.delete: image
	docker run --rm \
		-v $(HOME)/.ocm.json:/home/ansible/.ocm.json \
		-v $(HOME)/.aws:/home/ansible/.aws \
	  -ti quay.io/pczar/ansible-rosa \
		$(ANSIBLE) -v delete-cluster.yaml


galaxy.build:
	ansible-galaxy collection build --force .

galaxy.publish:
	VERSION=$$(yq e '.version' galaxy.yml); \
	ansible-galaxy collection publish rh_mobb-rosa-$$VERSION.tar.gz --api-key=$$ANSIBLE_GALAXY_API_KEY
