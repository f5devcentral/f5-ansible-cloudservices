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
module: f5_cs_catalog_items
short_description: Manage F5 CS Catalog Items
description: 
    - This module will manage Subscribed Services for F5 CloudServices
version_added: 1.0
options:
    state:
        description:
            - When C(present), will subscribe to service
            - When C(fetch), will fetch subscribed services
            - When C(absent), will remove unsubscribe from service
        default: present
        choices:
            - present
            - fetch
            - absent
    service:
        description: catalog service
        choices:
            - eap
            - dnslb
            - dns

author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: 
    - The examples can be found in /examples/f5_cs_catalog_items.yml
'''

RETURN = r'''
account_id:
    description: associated account id
catalog_id:
    description: service catalog id
catalog_items:
    description: list of subscribed services
status:
    description: service status
billing_provider:
    description: billing provider
trial_end_time:
    description: trial end time
contract_end_time:
    description: contract end time
create_time:
    description: create time
update_time:
    description: update time
delete_time:
    description: delete time
service:
    description: catalog service name
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
        'account_id',
        'catalog_id',
        'catalog_items',
        'status',
        'service',
        'billing_provider',
        'trial_end_time',
        'contract_end_time',
        'create_time',
        'update_time',
        'delete_time',
    ]

    returnables = [
        'account_id',
        'catalog_id',
        'catalog_items',
        'status',
        'billing_provider',
        'trial_end_time',
        'contract_end_time',
        'create_time',
        'update_time',
        'delete_time',
        'service',
    ]


class ApiParameters(Parameters):
    @property
    def account_id(self):
        return self._values['account_id']

    @property
    def catalog_id(self):
        return self._values['catalog_id']

    @property
    def catalog_items(self):
        return self._values['catalog_items']

    @property
    def status(self):
        return self._values['status']

    @property
    def billing_provider(self):
        return self._values['billing_provider']

    @property
    def trial_end_time(self):
        return self._values['trial_end_time']

    @property
    def contract_end_time(self):
        return self._values['contract_end_time']

    @property
    def create_time(self):
        return self._values['create_time']

    @property
    def update_time(self):
        return self._values['update_time']

    @property
    def delete_time(self):
        return self._values['delete_time']


class ModuleParameters(Parameters):
    @property
    def state(self):
        return self._values['state']

    @property
    def account_id(self):
        return self._values['account_id']

    @property
    def catalog_id(self):
        if self._values['catalog_id']:
            return self._values['catalog_id']
        if self._values['service']:
            mapping = {
                'dns': 'c-aaxBJkfg8u',
                'gslb': 'c-aaQnOrPjGu',
                'eap': 'c-aa9N0jgHI4',
                'beacon': 'c-aacHacMCM8',
            }
            return mapping.get(self._values['service'], None)
        return None

    @property
    def service(self):
        if self._values['service']:
            return self._values['service']
        if self._values['catalog_id']:
            mapping = {
                'c-aaxBJkfg8u': 'dns',
                'c-aaQnOrPjGu': 'gslb',
                'c-aa9N0jgHI4': 'eap',
                'c-aacHacMCM8': 'beacon',
            }
            return mapping.get(self._values['catalog_id'], None)
        return None


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
    pass


class ReportableChanges(Changes):
    pass


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

    def _diff_complex_items(self, want, have):
        if want == [] and have is None:
            return None
        if want is None and have:
            return have
        w = self.to_tuple(want)
        h = self.to_tuple(have)
        if set(w).issubset(set(h)):
            return None
        else:
            return want

    @property
    def catalog_id(self):
        if self.have.catalog_id:
            return self.have.catalog_id
        return self.want.catalog_id

    @property
    def account_id(self):
        if self.have.account_id:
            return self.have.account_id
        return self.want.account_id

    @property
    def service(self):
        if self.have.service:
            return self.have.service
        return self.want.service

    @property
    def catalog_items(self):
        return self.have.catalog_items

    @property
    def status(self):
        return self.have.status

    @property
    def billing_provider(self):
        return self.have.billing_provider

    @property
    def trial_end_time(self):
        return self.have.trial_end_time

    @property
    def contract_end_time(self):
        return self.have.contract_end_time

    @property
    def create_time(self):
        return self.have.create_time

    @property
    def update_time(self):
        return self.have.update_time

    @property
    def delete_time(self):
        return self.have.delete_time


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = kwargs.pop('client')
        self.want = ModuleParameters(params=self.module.params, client=self.client)
        self.have = ApiParameters(client=self.client)
        self.changes = UsableChanges()
        if self.want.account_id:
            self.client.account_id = self.want.account_id

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
        changed = False
        result = dict()
        state = self.want.state

        if state == 'present':
            changed = self.subscribe()
        elif state == 'fetch':
            if self.want.account_id is None and self.want.service is None:
                self.read_all_catalogs_from_cloud()
            else:
                self.get_catalog_from_cloud()
        elif state == 'absent':
            changed = self.unsubscribe()

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

    def get_account_id(self):
        if self.want.account_id:
            return self.want.account_id
        current_user = self.client.get_current_user()
        return current_user['primary_account_id']

    def get_catalog_services(self):
        response = self.client.get_account(account_id=self.get_account_id())
        return response.get('catalog_items', [])

    def subscribe(self):
        result = False
        services = self.get_catalog_services()
        account = ([x for x in services if x['catalog_id'] == self.want.catalog_id and x['status'] == 'SUBSCRIBED'] or [None])[0]
        if account is None:
            payload = {
                'account_id': self.want.account_id,
                'catalog_id': self.want.catalog_id,
            }

            self.have = ApiParameters(params=self.client.enable_catalog_item(payload, self.want.account_id))
            result = True
        else:
            self.have = ApiParameters(params=account)
        self._update_changed_options()
        return result

    def unsubscribe(self):
        result = False
        services = self.get_catalog_services()
        account = ([x for x in services if x['catalog_id'] == self.want.catalog_id and x['status'] == 'SUBSCRIBED'] or [None])[0]
        if account:
            self.have = ApiParameters(params=self.client.disable_catalog_item(self.get_account_id(), self.want.catalog_id))
            result = True
        else:
            self.have = ApiParameters(params=account)
        self._update_changed_options()
        return result

    def read_all_catalogs_from_cloud(self):
        services = self.get_catalog_services()
        self.have = ApiParameters(params=dict(catalog_items=services))
        self._update_changed_options()

    def get_catalog_from_cloud(self):
        services = self.get_catalog_services()
        service = ([x for x in services if x['catalog_id'] == self.want.catalog_id] or [None])[0]
        if service is None:
            raise F5ModuleError('service not found')
        self.have = ApiParameters(params=service)
        self._update_changed_options()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False
        argument_spec = dict(
            account_id=dict(),
            catalog_id=dict(),
            service=dict(
                default=None,
                choices=['dns', 'dnslb', 'eap']
            ),
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
