FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt install -y software-properties-common git \
    && apt-add-repository --yes --update ppa:ansible/ansible \
    && apt-add-repository --yes --update ppa:deadsnakes/ppa \
    && apt install -y python3-pip ansible ansible-test python3-yaml

RUN mkdir /var/workdir/
WORKDIR /var/workdir

COPY ./requirements.txt /var/workdir
RUN pip3 install -r requirements.txt

COPY . /var/workdir
RUN ansible-galaxy collection build --force
RUN ansible-galaxy collection install f5devcentral-cloudservices-1.0.0.tar.gz -f -p ./examples/collections/
