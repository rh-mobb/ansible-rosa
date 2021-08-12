#
# BUILD
#

FROM fedora:33 as build

ENV HOME=/home/ansible

RUN dnf -y install \
    bash gcc musl-devel libffi-devel git gpgme-devel libxml2-devel \
    libxslt-devel curl cargo openssl-devel python-devel unzip

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


FROM fedora:33

ENV HOME=/home/ansible

# # update the image
RUN dnf -y install \
    bash openssl unzip glibc groff

RUN groupadd ansible --g 1000 && useradd -s /bin/bash -g ansible -u 1000 ansible -d ${HOME}
RUN mkdir -p /ansible/virtualenv && chown -R ansible:ansible /ansible

# # copy executables from build image
# COPY --from=build /usr/local/bin /usr/local/bin

COPY --chown=ansible:ansible . /ansible
COPY --chown=ansible:ansible --from=build ${HOME}/.local ${HOME}/.local
COPY --chown=ansible:ansible --from=build /ansible/virtualenv /ansible/virtualenv

USER ansible:ansible

# # set pathing
ENV PATH=${HOME}/.local/bin:./virtualenv/bin:/ansible/staging/bin:$PATH
ENV PYTHONPATH=./virtualenv/lib/python3.8/site-packages/
ENV ANSIBLE_PYTHON_INTERPRETER=./virtualenv/bin/python
# # set kubeconfig and ansible options
ENV KUBECONFIG=/ansible/staging/.kube/config
ENV ANSIBLE_FORCE_COLOR=1

WORKDIR /ansible
