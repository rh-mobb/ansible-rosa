.DEFAULT_GOAL := help
.PHONY: help virtualenv kind image deploy

VIRTUALENV ?= "./virtualenv/"
ANSIBLE = $(VIRTUALENV)/bin/ansible-playbook

help:
	@echo GLHF

virtualenv:
	python3 -m venv $(VIRTUALENV)
	. $(VIRTUALENV)/bin/activate
	./virtualenv/bin/pip3 install -r requirements.txt --use-feature=2020-resolver

image:
	 docker build -t paulczar/ansible-rosa .

bootstrap:
	$(ANSIBLE) bootstrap.yaml

create:
	$(ANSIBLE) create.yaml

delete:
	$(ANSIBLE) delete.yaml



