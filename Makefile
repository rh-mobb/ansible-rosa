.DEFAULT_GOAL := help
.PHONY: help virtualenv kind image deploy

VIRTUALENV ?= "./virtualenv/"
ANSIBLE = $(VIRTUALENV)/bin/ansible-playbook

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
	$(ANSIBLE) -v create-cluster.yaml

delete:
	$(ANSIBLE) -v delete-cluster.yaml

create.multiaz:
	$(ANSIBLE) -v create-cluster.yaml -i ./environment/multi-az/hosts

create.private:
	$(ANSIBLE) -v create-cluster.yaml -i ./environment/private-link/hosts

delete.private:
	$(ANSIBLE) -v delete-cluster.yaml -i ./environment/private-link/hosts

delete.multiaz:
	$(ANSIBLE) -v delete-cluster.yaml -i ./environment/multi-az/hosts

create.tgw:
	$(ANSIBLE) -v create-cluster.yaml -i ./environment/transit-gateway-egress/hosts

delete.tgw:
	$(ANSIBLE) -v delete-cluster.yaml -i ./environment/transit-gateway-egress/hosts

create.hcp:
	$(ANSIBLE) -v create-cluster.yaml -i ./environment/hcp/hosts

delete.hcp:
	$(ANSIBLE) -v delete-cluster.yaml -i ./environment/hcp/hosts


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
