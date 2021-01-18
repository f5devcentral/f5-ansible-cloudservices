#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
import uuid

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: f5_cs_dnslb_ip_endpoints
short_description: Update IP Endpoints list
description: This module will add, remove and update DNSLB IP Endpoints list
version_added: 1.0
options:
    subscription_id:
        description: ID of existing subscription
    ip_endpoints:
        description: List of IP endpoints
        type: complex
        contains:
            virtual_server_type:
                description: Record type
                required: True
                default: cloud
                choices:
                    - vip-id
                    - cloud
            name:
                description: IP Endpoint name
                default: guid
            display_name:
                description: IP Endpoint display name
                default: guid
            port:
                description: port of the clients app
                default: 80
            translation_address:
                description: LTM translation address
            vip_id:
                description: BigIP VIP id
            address:
                description: IP address of the clients app
            monitor:
                description: health check monitor
                default: none
    account_id:
        description: ID of your main user’s primary account (where you will create instances)
    append:
        description: append IPs
        default: False
    state:
        description:
            - When C(absent), will remove provided IPs from the DNSLB application
            - When C(present) will replace DNSLB ips list with provided
        default: present
        choices:
            - present
            - absent
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: The examples can be found in /examples/f5_cs_dnslb_ip_endpoints.yml
'''

RETURN = r'''
subscription_id:
    description: ID of the changed DNSLB application
    sample: s-xxxxxxxxxx
ip_endpoints:
    description: List of IP endpoints
    type: complex
    contains:
        virtual_server_type:
            description: Record type, can be vip-id or cloud
            required: True
            default: cloud
            choices:
                - vip-id
                - cloud
        name:
            description: IP Endpoint name
            default: guid
        display_name:
            description: IP Endpoint display name
            default: guid
        port:
            description: port of the clients app
            default: 80
        translation_address:
            description: LTM translation address
        vip_id:
            description: BigIP VIP id
        address:
            description: IP address of the clients app
        monitor:
            description: health check monitor
            default: none
'''

try:
    from library.module_utils.cloudservices import CloudservicesApi
    from library.module_utils.common import F5ModuleError
    from library.module_utils.common import AnsibleF5Parameters
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import CloudservicesApi
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.common import F5ModuleError
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.common import AnsibleF5Parameters


class Parameters(AnsibleF5Parameters):
    updatables = [
        'subscription_id', 'ip_endpoints', 'configuration'
    ]

    returnables = [
        'subscription_id', 'ip_endpoints'
    ]


class ApiParameters(Parameters):
    @property
    def ip_endpoints(self):
        try:
            return self._values['configuration']['gslb_service']['virtual_servers']
        except Exception:
            return dict()

    @property
    def configuration(self):
        if self._values['configuration'] is None:
            return None
        return self._values['configuration']

    @property
    def account_id(self):
        return self._values['account_id']

    @property
    def catalog_id(self):
        return self._values['catalog_id']

    @property
    def service_instance_name(self):
        return self._values['service_instance_name']


class ModuleParameters(Parameters):
    @property
    def subscription_id(self):
        if self._values['subscription_id'] is None:
            return None
        return self._values['subscription_id']

    @property
    def ip_endpoints(self):
        return self._values['ip_endpoints']

    @property
    def state(self):
        return self._values['state']

    @property
    def append(self):
        return self._values['append']


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def configuration(self):
        if self._values['configuration'] is None:
            return None
        return self._values['configuration']


class ReportableChanges(Changes):
    @property
    def ip_endpoints(self):
        ip_endpoints = list()
        for key, value in self._values['ip_endpoints'].items():
            value['name'] = key
            ip_endpoints.append(value)
        return ip_endpoints


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def configuration(self):
        config = self.have.configuration
        w_ips = self.want.ip_endpoints
        h_ips = self.have.ip_endpoints
        ip_list = dict()
        if self.want.state == 'present' and self.want.append is False:
            for ip in w_ips:
                if not ip['name']:
                    ip['name'] = 'ipEndpoint_{0}'.format(str(uuid.uuid1()).replace('-', '_'))
                ip_list[ip['name']] = {k: v for k, v in iter(ip.items()) if v and k != 'name'}
                if not ip_list[ip['name']]['display_name']:
                    ip_list[ip['name']]['display_name'] = ip['name']
        elif self.want.state == 'present' and self.want.append is True:
            ip_list = h_ips
            for ip in w_ips:
                if not ip['name']:
                    ip['name'] = 'ipEndpoint_{0}'.format(str(uuid.uuid1()).replace('-', '_'))
                ip_list[ip['name']] = {k: v for k, v in iter(ip.items()) if v and k != 'name'}
                if not ip_list[ip['name']]['display_name']:
                    ip_list[ip['name']]['display_name'] = ip['name']
        elif self.want.state == 'absent':
            ip_list = h_ips
            for ip in w_ips:
                if ip['name'] in ip_list:
                    del ip_list[ip['name']]

        config['gslb_service']['virtual_servers'] = ip_list

        return config

    @property
    def subscription_id(self):
        return self.have.subscription_id

    @property
    def ip_endpoints(self):
        return self.have.ip_endpoints


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = kwargs.pop('client', None)
        self.want = ModuleParameters(params=self.module.params, client=self.client)
        self.have = ApiParameters(client=self.client)
        self.changes = UsableChanges()

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def exec_module(self):
        result = dict()

        changed = self.update_current()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def update_current(self):
        self.read_from_cloud(subscription_id=self.want.subscription_id)

        payload = {
            'subscription_id': self.have.subscription_id,
            'account_id': self.have.account_id,
            'catalog_id': self.have.catalog_id,
            'service_instance_name': self.have.service_instance_name,
            'configuration': self.changes.configuration,
        }

        if self.changes.configuration.get('details'):
            del self.changes.configuration['details']
        if self.changes.configuration.get('nameservers'):
            del self.changes.configuration['nameservers']
        payload['configuration'] = self.changes.configuration

        payload['configuration']['schemaVersion'] = '0.1'
        self.update_on_cloud(payload, subscription_id=self.want.subscription_id)
        return True

    def read_from_cloud(self, subscription_id):
        subscription = self.client.get_subscription_by_id(subscription_id)
        self.have = ApiParameters(params=subscription)
        self._update_changed_options()

    def update_on_cloud(self, payload, subscription_id):
        self.have = ApiParameters(params=self.client.update_subscription(payload, subscription_id))
        self._update_changed_options()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False

        ip_endpoint_spec = {
            'name': dict(
                default=None,
            ),
            'display_name': dict(
                default=None,
            ),
            'port': dict(
                default=80,
                type='int',
            ),
            'virtual_server_type': dict(
                default='cloud',
                choices=['cloud', 'bigip-ltm']
            ),
            'address': dict(
                default=None,
            ),
            'vip_id': dict(
                default=None,
            ),
            'remark': dict(
                default=None,
            ),
            'monitor': dict(
                default='none',
            ),
            'translation_address': dict(
                default=None,
            )
        }

        argument_spec = dict(
            subscription_id=dict(required=True),
            ip_endpoints=dict(type='list', elements='dict', options=ip_endpoint_spec),
            append=dict(type='bool', default=False),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
        )

        self.argument_spec = {}
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    connection = Connection(module._socket_path)
    client = CloudservicesApi(connection)

    try:
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
