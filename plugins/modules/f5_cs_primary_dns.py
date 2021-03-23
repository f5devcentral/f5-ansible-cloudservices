#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import time
import copy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: f5_cs_primary_dns
short_description: Manage Primary DNS Subscription
description: This module will manage Primary DNS application for F5 CloudServices
version_added: 1.0
options:
    subscription_id:
        description: ID of existing subscription
    service_instance_name:
        description:  Zone name or application name if Zone is specified in the configuration property
        required: True
    account_id:
        description: ID of your main user’s primary account (where you will create instances)
    state:
        description:
            - When C(absent), will remove Primary DNS subscription
            - When C(active), will activate Primary DNS subscription
            - When C(fetch), will return Primary DNS subscription
            - When C(present), will create or update Primary DNS subscription.
            - When C(suspended), will suspend Primary DNS subscription.
        default: present
        choices:
            - absent
            - active
            - fetch
            - present
            - suspended
    patch:
        description: When C(True), will merge provided configuration property with existing cloud configuration
        default: False
    zone:
        description: zone name
    configuration:
        description: Detailed Primary DNS application configuration
        type: complex
        contains:
            update_comment:
                description: Brief description of changes
                default: Update Primary DNS application
            dns_service:
                description: Describes Primary DNS service instance configuration.
    wait_status_change:
        description: wait until subscription is activated
        default: True
    activate:
        description: activate subscription on create
        default: True
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: The examples can be found in /examples/f5_cs_primary_dns.yml
'''

RETURN = r'''
subscription_id:
    description: ID of the new or changed Primary DNS application
    sample: s-xxxxxxxxxx
account_id:
    description: ID of the account with changes
    sample: a-xxxxxxxxxx
service_instance_name:
    description: Primary DNS application name or FQDN
    sample: fqdn.demo.net
configuration:
    description: The Primary DNS application configuration from the cloud
    type: complex
    contains:
        dns_service:
            description: Primary DNS configuration
            sample: Primary DNS Configuration
        details:
            description: Additional properties, such as CNAME or recommended zone list
            sample: Primary DNS Details
apps:
    description: list of available Primary DNS apps
status:
    description: subscription status
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
        'configuration', 'account_id', 'subscription_id', 'service_instance_name', 'status', 'apps'
    ]

    returnables = [
        'configuration', 'account_id', 'subscription_id', 'service_instance_name', 'status', 'apps'
    ]

    @property
    def description(self):
        if self._values['description'] is None:
            return ""
        return self._values['description']


class ApiParameters(Parameters):
    @property
    def configuration(self):
        if self._values['configuration'] is None:
            return None
        return self._values['configuration']

    @property
    def status(self):
        return self._values['status']

    @property
    def subscription_id(self):
        return self._values['subscription_id']

    @property
    def service_instance_name(self):
        return self._values['service_instance_name']

    @property
    def service_instance_id(self):
        return self._values['service_instance_id']

    @property
    def account_id(self):
        return self._values['account_id']


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
    def patch(self):
        return self._values['patch']

    @property
    def wait_status_change(self):
        return self._values['wait_status_change']

    @property
    def activate(self):
        return self._values['activate']

    @property
    def zone(self):
        if self._values['zone']:
            return self._values['zone']

        if self._values['service_instance_name']:
            return self._values['service_instance_name']
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
    @property
    def configuration(self):
        return self._values['configuration']


class ReportableChanges(Changes):
    @property
    def state(self):
        return self._values['status']


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
    def status(self):
        return self.have.status

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
        if self.want.patch:
            return dict(self._merge_dicts(self.have.configuration, self.want.configuration))

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
            if self.want.subscription_id:
                self.read_from_cloud(subscription_id=self.want.subscription_id)
            else:
                self.read_subscriptions_from_cloud()
        elif state == 'absent':
            if self.exists():
                changed = self.retire()
        elif state == 'active':
            if self.exists():
                changed = self.activate(self.have.subscription_id)
        elif state == 'suspended':
            if self.exists():
                changed = self.suspend(self.have.subscription_id)

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
            'subscription_id': self.have.subscription_id,
            'omit_config': True
        }
        self.remove_from_cloud(payload, subscription_id=self.have.subscription_id)
        return True

    def present(self):
        if self.exists():
            return self.update_current()
        else:
            return self.create()

    def exists(self):
        subscriptions = self.get_subscriptions()
        subscription = None
        if self.want.subscription_id:
            subscription = ([s for s in subscriptions if s['subscription_id'] == self.want.subscription_id] or [None])[0]
        else:
            subscription = \
                ([s for s in subscriptions if s['service_instance_name'] == self.want.service_instance_name] or [None])[0]
        if subscription is not None:
            self.have = ApiParameters(params=subscription)
            self._update_changed_options()
            return True
        return False

    def get_catalog_id(self):
        return 'c-aau0eSVXtL'

    def get_account_id(self):
        if self.want.account_id:
            return self.want.account_id
        current_user = self.client.get_current_user()
        return current_user['primary_account_id']

    def create(self):
        account_id = self.get_account_id()
        catalog_id = self.get_catalog_id()

        configuration = self.want.configuration

        if configuration is None:
            configuration = {
                "schemaVersion": "0.1",
                "id": "createPrimary",
                "dns_service": {
                    "zone": self.want.zone,
                    "accountId": account_id,
                    "owner": "dns-admin@f5cloudservices.com",
                    "primaryMaster": "ns1.f5cloudservices.com",
                    "ttl": 86400,
                    "refresh": 86400,
                    "retry": 7200,
                    "remark": "",
                    "expire": 360000,
                    "negative_ttl": 1800,
                }
            }

        payload = {
            "account_id": account_id,
            "catalog_id": catalog_id,
            "service_instance_name": self.want.service_instance_name,
            "service_type": "dns",
            "configuration": configuration,
        }
        self.create_on_cloud(payload)

        if self.want.activate:
            self.activate(self.have.subscription_id)

        return True

    def activate(self, subscription_id):
        state = self.client.activate_subscription(subscription_id)

        if not self.want.wait_status_change:
            return True

        for retry in range(0, 100):
            state = self.client.get_subscription_status(subscription_id)
            if state['status'] == 'ACTIVE' and state['service_state'] == 'DEPLOYED':
                break
            time.sleep(15)

        if state['status'] != 'ACTIVE' or state['service_state'] != 'DEPLOYED':
            raise F5ModuleError('cannot activate subscription: ' + state.status)
        return True

    def suspend(self, subscription_id):
        state = self.client.suspend_subscription(subscription_id)

        if not self.want.wait_status_change:
            return True

        for retry in range(0, 100):
            state = self.client.get_subscription_status(subscription_id)
            if state['status'] == 'DISABLED' and state['service_state'] == 'UNDEPLOYED':
                break
            time.sleep(15)

        if state['status'] != 'DISABLED' or state['service_state'] != 'UNDEPLOYED':
            raise F5ModuleError('cannot suspend subscription: ' + state['status'])

        self.have = ApiParameters(params=state)
        self._update_changed_options()
        return True

    def deep_changes_check(self, want, have, keys_check=False):
        if not want or not have:
            return want != have

        changed = False
        if isinstance(want, dict) and isinstance(have, dict):
            if keys_check is True and want.keys() != have.keys():
                return True
            for key in want.keys():
                w_value = want.get(key, None)
                h_value = have.get(key, None)
                if h_value is None:
                    changed = True
                    break
                if isinstance(w_value, dict):
                    changed = self.deep_changes_check(w_value, h_value)
                else:
                    changed = w_value != h_value

                if changed is True:
                    break
        else:
            changed = want != have
        return changed

    def update_current(self):
        changed = False
        catalog_id = self.get_catalog_id()
        payload = {
            'account_id': self.have.account_id,
            'catalog_id': catalog_id,
            'service_type': 'dns',
        }

        if self.want.configuration and self.want.patch is False:
            payload['configuration'] = self.want.configuration
            payload['service_instance_name'] = self.want.service_instance_name

            h_config = copy.deepcopy(self.have.configuration)
            if h_config.get('create_time', None):
                del h_config['create_time']
            if h_config.get('update_time', None):
                del h_config['update_time']
            if h_config.get('cancel_time', None):
                del h_config['cancel_time']
            if h_config.get('end_time', None):
                del h_config['end_time']
            if h_config.get('nameservers', None):
                del h_config['nameservers']
            if h_config.get('dns_service', None):
                if h_config['dns_service'].get('admin', None):
                    del h_config['dns_service']['admin']
                if h_config['dns_service'].get('primary_nameserver', None):
                    del h_config['dns_service']['primary_nameserver']

            changed = self.deep_changes_check(self.want.configuration, h_config, True)
            changed = changed or self.want.service_instance_name != self.have.service_instance_name
        else:
            payload['configuration'] = copy.deepcopy(self.changes.configuration)
            if payload['configuration'].get('create_time', None):
                del payload['configuration']['create_time']
            if payload['configuration'].get('update_time', None):
                del payload['configuration']['update_time']
            if payload['configuration'].get('cancel_time', None):
                del payload['configuration']['cancel_time']
            if payload['configuration'].get('end_time', None):
                del payload['configuration']['end_time']
            if payload['configuration'].get('nameservers', None):
                del payload['configuration']['nameservers']

            if payload['configuration'].get('dns_service', None):
                if payload['configuration']['dns_service'].get('admin', None):
                    del payload['configuration']['dns_service']['admin']
                if payload['configuration']['dns_service'].get('primary_nameserver', None):
                    del payload['configuration']['dns_service']['primary_nameserver']

            payload['service_instance_name'] = self.want.service_instance_name or self.have.service_instance_name
            if self.want.configuration:
                changed = self.deep_changes_check(self.want.configuration, self.have.configuration, False)
                changed = changed or payload['service_instance_name'] != self.have.service_instance_name

        if changed is True:
            payload['subscription_id'] = self.have.subscription_id
            payload['configuration']['dns_service']['id'] = self.have.subscription_id
            payload['configuration']['dns_service']['accountId'] = self.have.account_id
            payload['configuration']['schemaVersion'] = '0.1'
            payload['configuration']['update_comment'] = self.want.update_comment
            payload['configuration']['dns_service']['primaryMaster'] = "ns1.f5cloudservices.com"
            payload['configuration']['dns_service']['owner'] = "dns-admin@f5cloudservices.com"
            self.update_on_cloud(payload, subscription_id=self.have.subscription_id)
        return changed

    def get_subscriptions(self):
        account_id = self.get_account_id()
        response = self.client.get_subscriptions_by_type(subscription_type='dns', account_id=account_id)
        return response.get('subscriptions', [])

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
            configuration=dict(type=dict),
            state=dict(
                default='present',
                choices=['present', 'absent', 'fetch', 'active', 'suspended']
            ),
            update_comment=dict(default='update Primary DNS configuration'),
            patch=dict(
                default=False,
                type='bool',
            ),
            wait_status_change=dict(
                default=True,
                type='bool',
            ),
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
