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
module: f5_cs_organization
short_description: Manage F5 CS Organizations
description: 
    - This module will manage Organizations for F5 CloudServices
version_added: 1.0
options:
    state:
        description:
            - When C(present), will create or update Organization 
            - When C(fetch), will fetch Organizations
            - When C(absent), will remove Organization
        default: present
        choices:
            - present
            - fetch
            - absent
    account_id:
        description: organization account id
    parent_account_id:
        description: parent account id. If specified will create a sub-account
    name: 
        description: organization name
    address:
        street_1: 
        street_2: 
        city: 
            description: city
        state: 
            description: state 
        country: 
            description: country code
        postal_code: 
            description: zip code
    phone:
        description: phone
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: 
    - The examples can be found in /examples/f5_cs_organization.yml
'''

RETURN = r'''
account_id:
    description: organization account id
parent_account_id:
    description: parent account id. If specified will create a sub-account
name: 
    description: organization name
address:
    description: organization address
phone:
    description: phone
status:
    description: account status
accounts:
    description: all organizations list
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
        'name', 'account_id', 'parent_account_id', 'address', 'phone', 'status', 'accounts'
    ]

    returnables = [
        'name', 'account_id', 'parent_account_id', 'address', 'phone', 'status', 'accounts'
    ]


class ApiParameters(Parameters):
    @property
    def id(self):
        return self._values['id']

    @property
    def name(self):
        return self._values['name']

    @property
    def parent_account_id(self):
        return self._values['parent_account_id']

    @property
    def status(self):
        return self._values['status']

    @property
    def level(self):
        return self._values['level']

    @property
    def address(self):
        return self._values['address']

    @property
    def phone(self):
        return self._values['phone']

    @property
    def compliant(self):
        return self._values['compliant']

    @property
    def catalog_items(self):
        return self._values['catalog_items']

    @property
    def create_time(self):
        return self._values['create_time']

    @property
    def update_time(self):
        return self._values['update_time']

    @property
    def delete_time(self):
        return self._values['delete_time']

    @property
    def accounts(self):
        return self._values['accounts']


class ModuleParameters(Parameters):
    @property
    def state(self):
        return self._values['state']

    @property
    def name(self):
        return self._values['name']

    @property
    def parent_account_id(self):
        return self._values['parent_account_id']

    @property
    def address(self):
        return self._values['address']

    @property
    def phone(self):
        return self._values['phone']


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
    def name(self):
        return self.have.name

    @property
    def address(self):
        return self.have.address

    @property
    def account_id(self):
        return self.have.id

    @property
    def parent_account_id(self):
        return self.have.parent_account_id

    @property
    def phone(self):
        return self.have.phone

    @property
    def status(self):
        return self.have.status

    @property
    def accounts(self):
        return self.have.accounts


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = kwargs.pop('client', None)
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
            changed = self.present()
        elif state == 'fetch':
            if self.want.account_id is None and self.want.name is None:
                self.read_accounts_from_cloud()
            elif self.exists() is False:
                raise F5ModuleError('account not found')
        elif state == 'absent':
            if self.exists():
                changed = self.retire()

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

    def retire(self):
        payload = {
            'id': self.have.id,
            'omit_config': True
        }
        self.remove_from_cloud(payload, account_id=self.have.id)
        return True

    def present(self):
        if self.exists():
            return self.update_current()
        else:
            return self.create()

    def exists(self):
        if self.want.account_id:
            return self.check_account_on_cloud_by_id(self.want.account_id)
        elif self.want.name:
            return self.check_account_on_cloud_by_name(self.want.name)
        else:
            return False

    def create(self):
        payload = {
            'address': self.want.address,
            'name': self.want.name,
            'parent_account_id': self.want.parent_account_id or '',
            'phone': self.want.phone,
        }

        self.create_on_cloud(payload)
        return True

    def update_current(self):
        payload = {
            'id': self.want.account_id or self.have.id,
            'address': self.want.address or self.have.address,
            'name': self.want.name or self.have.name,
            'parent_account_id': self.want.parent_account_id or self.have.parent_account_id,
            'phone': self.want.phone or self.have.phone,
            'status': self.have.status,
        }

        changed = self.have.address != payload['address'] \
            or self.have.name != payload['name'] \
            or self.have.parent_account_id != payload['parent_account_id'] \
            or self.have.phone != payload['phone']

        if changed:
            self.update_on_cloud(payload, self.have.id)
        return changed

    def get_current_user_id(self):
        response = self.client.get_current_user()
        return response.get('id', None)

    def get_memberships(self):
        user_id = self.get_current_user_id()
        response = self.client.get_memberships(user_id)
        return response.get('memberships', [])

    def check_account_on_cloud_by_id(self, account_id):
        result = False
        accounts = self.get_memberships()
        account = ([x for x in accounts if x['account_id'] == account_id] or [None])[0]
        if account:
            self.have = ApiParameters(params=self.client.get_account(account['account_id']))
            self._update_changed_options()
            result = True
        return result

    def check_account_on_cloud_by_name(self, name):
        result = False
        accounts = self.get_memberships()
        account = ([x for x in accounts if x['account_name'] == name] or [None])[0]
        if account:
            self.have = ApiParameters(params=self.client.get_account(account['account_id']))
            self._update_changed_options()
            result = True
        return result

    def read_accounts_from_cloud(self):
        accounts = []
        memberships = self.get_memberships()
        for membership in memberships:
            accounts.append(self.client.get_account(membership['account_id']))
        self.have = ApiParameters(params=dict(accounts=accounts))
        self._update_changed_options()

    def update_on_cloud(self, payload, account_id):
        self.have = ApiParameters(params=self.client.update_account(payload, account_id))
        self._update_changed_options()

    def create_on_cloud(self, payload):
        self.have = ApiParameters(params=self.client.create_account(payload))
        self._update_changed_options()

    def remove_from_cloud(self, payload, account_id):
        response = self.client.delete_account(payload, account_id)
        self.have = ApiParameters(params=response)
        self._update_changed_options()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False
        argument_spec = dict(
            account_id=dict(),
            name=dict(),
            parent_account_id=dict(default=''),
            address=dict(
                type=dict,
                street_1=dict(),
                street_2=dict(default=''),
                city=dict(),
                state=dict(),
                country=dict(),
                postal_code=dict(),
            ),
            phone=dict(default=''),
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
