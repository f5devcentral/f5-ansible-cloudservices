Introduction
------------

This repository provides the foundation for working with the F5 Modules for Ansible.
The architecture of the modules makes inherent use of the F5 Cloud Services REST APIs.

This repository is an **incubator** for Ansible modules. The modules in this repository **may be
broken due to experimentation or refactoring**.

The F5 Modules for Ansible are freely provided to the open source community for automating F5 Cloud Services configurations.


Installing the Build
----------------------------

```shell

    # CASE 1
    # To install build from the repository
    git clone git@github.com:f5devcentral/f5-ansible-cloudservices.git
    cd ./f5-ansible-cloudservices
    ansible-galaxy collection build --force
    ansible-galaxy collection install f5devcentral-cloudservices-1.0.0.tar.gz -p ./collections/

    # CASE 2
    # To install from the Ansible Galaxy
    # Not yet available
    ansible-galaxy collection install f5devcentral-cloudservices -p ./collections/

    # CASE 3
    # Use Docker and docker-compose
    docker-compose up
```


**NOTE:** "-p" is the location in which the collection will be installed. This location should be defined in the path for
ansible to search for collections. An example of this would be adding ``collections_paths = ./collections``
to your **ansible.cfg**

Supported Services & Modules
----------------------------
The following F5 Cloud Services modules are currently supported:


**F5 Essential App Protect**:
Provides application protection (as a Service) across multiple attack vectors using signatures from F5 Labs threat intelligence. 

More info: 
https://clouddocs.f5.com/cloud-services/latest/f5-cloud-services-Essential.App.Protect-About.html

API User's Guide: https://clouddocs.f5.com/cloud-services/latest/f5-cloud-services-Essential.App.Protect-API.UsersGuide.html

**Modules**:
 - f5_cs_eap_certificate
 - f5_cs_eap_cname_fetch
 - f5_cs_eap_ip_enforcement
 - f5_cs_eap_subscription_app
 

Example Playbook
------------

Ansible modules are documented within each the .py code of each module itself within ``/plugins/modules/``. The example below will upload and apply certificate for an app protected by F5 Essential App Protect service.

```yml

    - name: Apply SSL certificate
      hosts: webservers
      gather_facts: false
      collections:
        - f5devcentral.cloudservices
      connection: httpapi

      vars:
        ansible_network_os: f5devcentral.cloudservices.f5
        ansible_host: "api.cloudservices.f5.com"
        ansible_user: "user@example.com"
        ansible_httpapi_password: "password"
        ansible_httpapi_use_ssl: yes

      tasks:
        - name: Apply SSL Certificate
          f5_cs_eap_certificate:
            subscription_id: "s-xxxxxxxxxx"
            certificate: "{{ lookup('file', './fqdn.cert') }}"
            private_key: "{{ lookup('file', './fqdn.key') }}"
            passphrase: "demo_ansible"
            certificate_chain: "{{ lookup('file', './chain.cert') }}"
            https_port: 443
            https_redirect: true
            update_comment: "update SSL certificate"
```

Bugs, Issues
------------

Please file any bugs, questions, or enhancement requests by using GitHub Issues

Documentation
-------------

All documentation is available inside the modules

Your ideas
----------

What types of modules do you want created? If you have a use case and can sufficiently describe the behavior you want to see, open an issue and we will hammer out the details.
