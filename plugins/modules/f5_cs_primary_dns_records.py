#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: f5_cs_primary_dns_records
short_description: Update DNS records
description: This module will add, remove and update Primary DNS records
version_added: 1.0
options:
    subscription_id:
        description: ID of existing subscription
    records:
        description: List of DNS records
        type: complex
    account_id:
        description: ID of your main user’s primary account (where you will create instances)
    append:
        description: append records
        default: True
    state:
        description:
            - When C(fetch), will fetch all available records
            - When C(absent), will remove provided record
            - When C(present) will replace records list with provided
        default: present
        choices:
            - present
            - absent
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: The examples can be found in /examples/f5_cs_primary_dns_records.yml
'''

RETURN = r'''
subscription_id:
    description: ID of the changed Primary DNS application
    sample: s-xxxxxxxxxx
records:
    description: List dns records
    type: complex
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
        'subscription_id', 'records', 'configuration'
    ]

    returnables = [
        'subscription_id', 'records'
    ]


class ApiParameters(Parameters):
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

    @property
    def records(self):
        if self._values['configuration'] is None:
            return None
        return self._values['configuration']['dns_service']['records']


class ModuleParameters(Parameters):
    @property
    def subscription_id(self):
        if self._values['subscription_id'] is None:
            return None
        return self._values['subscription_id']

    @property
    def records(self):
        return self._values['records']

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
        w_records = self.want.records
        h_records = self.have.records
        records = dict(h_records)
        if self.want.state == 'present' and self.want.append is False:
            records = w_records
        elif self.want.state == 'present' and self.want.append is True:
            for w_rec_key in set(w_records.keys()):
                records[w_rec_key] = w_records[w_rec_key]
        elif self.want.state == 'absent':
            for w_rec_key in set(w_records.keys()):
                if records.get(w_rec_key, None):
                    del records[w_rec_key]

        config['dns_service']['records'] = records
        return config

    @property
    def subscription_id(self):
        return self.have.subscription_id

    @property
    def records(self):
        return self.have.records


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
        changed = False

        if self.want.state == 'fetch':
            self.read_from_cloud(subscription_id=self.want.subscription_id)
        else:
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
        if self.changes.configuration.get('create_time', None):
            del self.changes.configuration['create_time']
        if self.changes.configuration.get('update_time', None):
            del self.changes.configuration['update_time']
        if self.changes.configuration.get('cancel_time', None):
            del self.changes.configuration['cancel_time']
        if self.changes.configuration.get('end_time', None):
            del self.changes.configuration['end_time']
        if self.changes.configuration.get('nameservers', None):
            del self.changes.configuration['nameservers']

        if self.changes.configuration.get('dns_service', None):
            self.changes.configuration['dns_service']['id'] = self.have.subscription_id,
            if self.changes.configuration['dns_service'].get('admin', None):
                del self.changes.configuration['dns_service']['admin']
            if self.changes.configuration['dns_service'].get('primary_nameserver', None):
                del self.changes.configuration['dns_service']['primary_nameserver']

        payload['configuration'] = self.changes.configuration

        if self.changes.configuration.get('nameservers', None):
            del self.changes.configuration['nameservers']

        payload['configuration']['schemaVersion'] = '0.1'
        self.update_on_cloud(payload, subscription_id=self.want.subscription_id)
        return True

    def read_from_cloud(self, subscription_id):
        subscription = self.client.get_subscription_by_id(subscription_id)
        self.have = ApiParameters(params=subscription)
        self._update_changed_options()

    def update_on_cloud(self, payload, subscription_id):
        subscription = self.client.update_subscription(payload, subscription_id)
        self.have = ApiParameters(params=subscription)
        self._update_changed_options()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False

        argument_spec = dict(
            subscription_id=dict(required=True),
            records=dict(type='dict'),
            append=dict(type='bool', default=True),
            state=dict(
                default='present',
                choices=['present', 'absent', 'fetch']
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
