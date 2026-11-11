#
# BUILD — Python 3.11+ required (ocm-python 0.4.0)
#

FROM fedora:41 as build

ENV HOME=/home/ansible

RUN dnf -y install \
    bash gcc git libffi-devel openssl-devel python3-devel \
    libxml2-devel libxslt-devel curl unzip \
    && dnf clean all

RUN groupadd ansible --g 1000 && useradd -s /bin/bash -g ansible -u 1000 ansible -d ${HOME}

RUN mkdir -p /ansible/virtualenv && chown -R ansible:ansible /ansible

USER ansible:ansible

RUN mkdir -p ${HOME}/.local/bin

WORKDIR /ansible

# add other executables
RUN curl -slL https://storage.googleapis.com/kubernetes-release/release/v1.18.3/bin/linux/amd64/kubectl \
        -o kubectl && install kubectl ${HOME}/.local/bin/
RUN curl -slL https://github.com/openshift/rosa/releases/download/v1.1.0/rosa-linux-amd64 \
        -o rosa && install rosa ${HOME}/.local/bin/
RUN curl -slL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip \
        -o awscli.zip && unzip awscli.zip && aws/install -i ${HOME}/.local/aws-cli -b /ansible/.local/bin

COPY ./requirements.txt /ansible/requirements.txt

RUN python3 -m venv /ansible/virtualenv
RUN /ansible/virtualenv/bin/python3 -m pip install --upgrade pip
RUN /ansible/virtualenv/bin/pip3 install -r /ansible/requirements.txt

COPY . /ansible


FROM fedora:41

ENV HOME=/home/ansible

RUN dnf -y install \
    bash openssl unzip glibc groff \
    && dnf clean all

RUN groupadd ansible --g 1000 && useradd -s /bin/bash -g ansible -u 1000 ansible -d ${HOME}
RUN mkdir -p /ansible/virtualenv && chown -R ansible:ansible /ansible

COPY --chown=ansible:ansible . /ansible
COPY --chown=ansible:ansible --from=build ${HOME}/.local ${HOME}/.local
COPY --chown=ansible:ansible --from=build /ansible/virtualenv /ansible/virtualenv

USER ansible:ansible

ENV PATH=${HOME}/.local/bin:./virtualenv/bin:/ansible/staging/bin:$PATH
ENV ANSIBLE_PYTHON_INTERPRETER=./virtualenv/bin/python
ENV KUBECONFIG=/ansible/staging/.kube/config
ENV ANSIBLE_FORCE_COLOR=1

WORKDIR /ansible
