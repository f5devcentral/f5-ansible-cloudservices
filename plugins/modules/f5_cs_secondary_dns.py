#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: f5_cs_secondary_dns
short_description: Manage DNS Subscription
description: This module will manage DNS for F5 CloudServices
version_added: 1.0
options:
    subscription_id:
        description: ID of existing subscription
    account_id:
        description: ID of your main user’s primary account (where you will create instances)
    service_instance_name:
        description:  zone name
    configuration:
        description: detailed DNS configuration
    state:
        description:
            - When C(present), will create or update DNS subscription.
            - When C(absent), will remove DNS subscription
            - When C(fetch) will return subscription configuration by subscription_id of all subscriptions if not subscription id is not provided
            - When C(active) will activate subscription
            - When C(suspended) will suspend subscription
        default: present
        choices:
            - present
            - absent
            - fetch
            - active
            - suspended

author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description:
    - The examples can be found in /examples/f5_cs_secondary_dns.yml
'''

RETURN = r'''
subscription_id:
    description: ID of the new or changed DNS application
    sample: s-xxxxxxxxxx
account_id:
    description: ID of the account with changes
    sample: a-xxxxxxxxxx
configuration:
    description: detailed DNS configuration
service_instance_name:
    description: DNS zone name
apps:
    description: list of all available DNS subscriptions
state:
    description: DNS subscription state
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
        'configuration', 'account_id', 'service_instance_name', 'subscription_id', 'state', 'apps'
    ]

    returnables = [
        'configuration', 'account_id', 'service_instance_name', 'subscription_id', 'state', 'apps'
    ]


class ApiParameters(Parameters):
    @property
    def configuration(self):
        return self._values['configuration']

    @property
    def status(self):
        return self._values['status']

    @property
    def apps(self):
        return self._values['apps']


class ModuleParameters(Parameters):
    @property
    def configuration(self):
        return self._values['configuration']

    @property
    def subscription_id(self):
        if self._values['subscription_id'] is None:
            return None
        return self._values['subscription_id']

    @property
    def account_id(self):
        return self._values['account_id']

    @property
    def activate(self):
        return self._values['activate']


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
        return self._values['configuration']


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
    def subscription_id(self):
        return self.have.subscription_id

    @property
    def account_id(self):
        return self.have.account_id

    @property
    def service_instance_name(self):
        return self.have.service_instance_name

    def _merge_dicts(self, dict1, dict2):
        for k in set(dict1.keys()).union(dict2.keys()):
            if k in dict1 and k in dict2:
                if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                    yield k, dict(self._merge_dicts(dict1[k], dict2[k]))
                else:
                    yield k, dict2[k]
            elif k in dict1:
                yield k, dict1[k]
            else:
                yield k, dict2[k]

    @property
    def configuration(self):
        return self.have.configuration

    @property
    def apps(self):
        return self.have.apps


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
            if self.want.subscription_id is None and self.want.service_instance_name is None:
                self.read_subscriptions_from_cloud()
            elif self.exists() is False:
                raise F5ModuleError('subscription not found')
        elif state == 'absent':
            if self.exists():
                changed = self.retire()
        elif state == 'active':
            if self.exists():
                changed = self.activate()
        elif state == 'suspended':
            if self.exists():
                changed = self.suspend()

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
        result = False
        if self.exists():
            payload = {
                'subscription_id': self.want.subscription_id,
                'omit_config': True
            }
            self.remove_from_cloud(payload, subscription_id=self.want.subscription_id)
            result = True
        return result

    def present(self):
        if self.exists():
            return self.update_current()
        else:
            return self.create()

    def exists(self):
        if self.want.service_instance_name:
            return self.check_subscription_on_cloud_by_zone_name(self.want.service_instance_name)
        elif self.want.subscription_id:
            return self.check_subscription_on_cloud_by_subscription_id(self.want.subscription_id)
        else:
            return False

    def get_catalog_id(self):
        if self.want.catalog_id:
            return self.want.catalog_id
        catalogs = self.client.get_catalogs()
        dns_catalog = next(c for c in catalogs['Catalogs'] if c['service_type'] == 'adns')
        return dns_catalog['catalog_id']

    def get_account_id(self):
        if self.want.account_id:
            return self.want.account_id
        current_user = self.client.get_current_user()
        return current_user['primary_account_id']

    def get_default_configuration(self):
        return dict(
            adns_service=dict(
                zone=self.want.service_instance_name,
                master_servers=self.want.master_servers,
            )
        )

    def create(self):
        account_id = self.get_account_id()
        catalog_id = self.get_catalog_id()

        payload = {
            'account_id': account_id,
            'catalog_id': catalog_id,
            'service_instance_name': self.want.service_instance_name,
            'service_type': 'adns',
            'configuration': self.want.configuration or self.get_default_configuration(),
        }
        self.create_on_cloud(payload)

        if self.want.activate is True:
            self.activate()

        return True

    def activate(self):
        if self.have.status == 'ACTIVE':
            return False

        state = self.client.activate_subscription(self.have.subscription_id)

        for retry in range(0, 100):
            state = self.client.get_subscription_status(self.have.subscription_id)
            if state['status'] == 'ACTIVE':
                break
            time.sleep(15)

        if state['status'] != 'ACTIVE':
            raise F5ModuleError('cannot activate subscription: ' + state.status)

        self.have.update(dict(status=state['status']))
        return True

    def suspend(self):
        if self.have.status == 'DISABLED':
            return False

        state = self.client.suspend_subscription(subscription_id=self.want.subscription_id)

        for retry in range(0, 100):
            state = self.client.get_subscription_status(subscription_id=self.want.subscription_id)
            if state['status'] == 'DISABLED' and state['service_state'] == 'UNDEPLOYED':
                break
            time.sleep(15)

        if state['status'] != 'DISABLED' or state['service_state'] != 'UNDEPLOYED':
            raise F5ModuleError('cannot suspend subscription: ' + state.status)

        self.have.update(dict(status=state['status']))
        return True

    def update_current(self):
        payload = {
            'account_id': self.have.account_id,
            'catalog_id': self.have.catalog_id,
            'service_instance_name': self.have.service_instance_name,
            'service_type': 'gslb',
            'configuration': self.want.configuration or self.get_default_configuration(),
        }

        changed = self.have.configuration['adns_service']['master_servers'].sort() != payload['configuration']['adns_service']['master_servers'].sort() \
            or self.have.configuration['adns_service']['zone'] != payload['configuration']['adns_service']['zone']

        if changed:
            self.update_on_cloud(payload, subscription_id=self.want.subscription_id)
        return changed

    def get_subscriptions(self):
        account_id = self.get_account_id()
        response = self.client.get_subscriptions_by_type(subscription_type='adns', account_id=account_id)
        return response.get('subscriptions', [])

    def check_subscription_on_cloud_by_subscription_id(self, subscription_id):
        result = False
        subscriptions = self.get_subscriptions()
        subscription = ([x for x in subscriptions if x['subscription_id'] == subscription_id] or [None])[0]
        if subscription:
            self.have = ApiParameters(params=subscription)
            self._update_changed_options()
            result = True
        return result

    def check_subscription_on_cloud_by_zone_name(self, service_instance_name):
        result = False
        subscriptions = self.get_subscriptions()
        subscription = ([x for x in subscriptions if x['service_instance_name'] == service_instance_name] or [None])[0]
        if subscription:
            self.have = ApiParameters(params=subscription)
            self._update_changed_options()
            result = True
        return result

    def read_subscriptions_from_cloud(self):
        subscriptions = self.get_subscriptions()
        self.have = ApiParameters(params=dict(apps=subscriptions))
        self._update_changed_options()

    def read_from_cloud(self, subscription_id):
        subscription = self.client.get_subscription_by_id(subscription_id)
        self.have = ApiParameters(params=subscription)
        self._update_changed_options()

    def update_on_cloud(self, payload, subscription_id):
        self.have = ApiParameters(params=self.client.update_subscription(payload, subscription_id))
        self._update_changed_options()

    def create_on_cloud(self, payload):
        self.have = ApiParameters(params=self.client.create_subscription(payload))
        self._update_changed_options()

    def remove_from_cloud(self, payload, subscription_id):
        response = self.client.retire_subscription(payload, subscription_id)
        self.have = ApiParameters(params=response)
        self._update_changed_options()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False
        argument_spec = dict(
            subscription_id=dict(),
            account_id=dict(),
            service_instance_name=dict(),
            master_servers=dict(type=list),
            configuration=dict(type=dict),
            state=dict(
                default='present',
                choices=['present', 'absent', 'fetch', 'active', 'suspended']
            ),
            update_comment=dict(default='update DNS configuration'),
            activate=dict(
                type='bool',
                default=True,
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
