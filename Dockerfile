FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt install -y software-properties-common git \
    && apt install -y python-pip

RUN mkdir /var/workdir/
WORKDIR /var/workdir

COPY ./requirements.txt /var/workdir
RUN pip install -r requirements.txt

COPY . /var/workdir
RUN ansible-galaxy collection build --force
RUN ansible-galaxy collection install f5devcentral-cloudservices-1.0.1.tar.gz -f -p ./examples/collections/

CMD ["bash", "run.sh"]