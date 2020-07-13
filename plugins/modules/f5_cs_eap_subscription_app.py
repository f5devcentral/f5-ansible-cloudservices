#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type
import time

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: f5_cs_eap_subscription_app
short_description: Manage EAP Subscription
description: 
    - This module will manage Essential App Protect application for F5 CloudServices
version_added: 1.0
options:
    subscription_id:
        description:
            - ID of existing subscription
    service_instance_name:
        description:
            - FQDN record name or application name if FQDN was specified in the configuration property
        required: True            
    account_id:
        description:
            - ID of your main user’s primary account (where you will create instances)
    state:
        description:
            - When C(present), will create or update EAP subscription. 
            - When C(absent), will remove EAP subscription
            - When C(fetch) will return subscription configuration by subscription_id
        default: present
        choices:
            - present
            - absent
            - fetch
    patch:
        description:
            - When C(True), will merge provided configuration property with existing cloud configuration
        default: False
    activate:
        description:
            - When C(True), will activate subscription on create
        default: True
    configuration:
        update_comment:
            description: 
                - Brief description of changes
            default: Update EAP application
        waf_service:
            description: 
                - Describes Essential App Protect service instance configuration. 
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: 
    - The examples can be found in /examples/f5_cs_eap_subscription_app.yml
'''

RETURN = r'''
subscription_id
    description: ID of the new or changed EAP application
    sample: s-xxxxxxxxxx
account_id
    description: ID of the account with changes
    sample: a-xxxxxxxxxx
service_instance_name
    description: EAP application name or FQDN
    sample: fqdn.demo.net
configuration
    description: The EAP application configuration from the cloud
    returned: changed
    type: complex
    contains:
        waf_service:
            description: EAP configuration
            sample: EAP Configuration
        details:
            description: Additional properties, such as CNAME or recommended zone list
            sample: EAP Details
'''

try:
    from library.module_utils.cloudservices import HttpRestApi
    from library.module_utils.cloudservices import HttpConnection
    from library.module_utils.cloudservices import F5ModuleError
    from library.module_utils.cloudservices import f5_cs_argument_spec
    from library.module_utils.cloudservices import f5_cs_eap_default_policy
    from library.module_utils.cloudservices import AnsibleF5Parameters
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import HttpRestApi
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import HttpConnection
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import F5ModuleError
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import f5_cs_argument_spec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import f5_cs_eap_default_policy
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import AnsibleF5Parameters


class Parameters(AnsibleF5Parameters):
    updatables = [
        'configuration', 'account_id', 'catalog_id', 'subscription_id', 'service_instance_name', 'status'
    ]

    returnables = [
        'configuration', 'account_id', 'catalog_id', 'subscription_id', 'service_instance_name', 'status'
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
    def catalog_id(self):
        return self.have.catalog_id

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


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = kwargs.pop('client', None)
        self.want = ModuleParameters(params=self.module.params, client=self.client)
        self.have = ApiParameters(client=self.client)
        self.changes = UsableChanges()

        f5_cs = self.module.params.get('f5_cloudservices', None)
        self.username = f5_cs['user']
        self.password = f5_cs['password']
        self.client.login(self.username, self.password)

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
            self.read_from_cloud(subscription_id=self.want.subscription_id)
        elif state == 'absent':
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
            'subscription_id': self.want.subscription_id,
            'omit_config': True
        }
        self.remove_from_cloud(payload, subscription_id=self.want.subscription_id)
        return True

    def present(self):
        if self.exists():
            return self.update_current()
        else:
            return self.create()

    def exists(self):
        if self.want.subscription_id:
            return True
        else:
            return False

    def get_catalog_id(self):
        if self.want.catalog_id:
            return self.want.catalog_id
        catalogs = self.client.get_catalogs()
        eap_catalog = next(c for c in catalogs['Catalogs'] if c['service_type'] == 'waf')
        return eap_catalog['catalog_id']

    def get_account_id(self):
        if self.want.account_id:
            return self.want.account_id
        current_user = self.client.get_current_user()
        return current_user['primary_account_id']

    def auto_discover(self, account_id, catalog_id):
        payload = {
            'account_id': account_id,
            'catalog_id': catalog_id,
            'service_instance_name': self.want.service_instance_name,
            'service_type': 'waf',
            'configuration': {
                'waf_service': {
                    'application': {
                        'description': self.want.service_instance_name,
                        'fqdn': self.want.service_instance_name,
                        'http': {
                            'enabled': True,
                            'port': 80,
                        },
                    },
                    'policy': {
                        'encoding': 'utf-8',
                    },
                },
            },
        }

        self.create_on_cloud(payload)

        discovery = None
        for retry in range(0, 12):
            time.sleep(10)
            subscription = self.client.get_subscription_by_id(self.have.subscription_id)
            if subscription['configuration'].get('details'):
                discovery = subscription['configuration']['details']['discovery']
                break

        if discovery is None:
            raise F5ModuleError('Auto discovery failed')

        return {
            'waf_service': {
                'application': {
                    'description': self.want.service_instance_name,
                    'fqdn': self.want.service_instance_name,
                    'http': {
                        'enabled': True,
                        'port': 80,
                    },
                    'https': {
                        'enabled': False,
                        'port': 443,
                        'tls': {
                            'certificate_id': '',
                        }
                    },
                    'waf_regions': {
                        discovery['cloudProvider']: {
                            discovery['cloudRegion']: {
                                'endpoint': {
                                    'http': {
                                        'port': 80,
                                        'enabled': discovery["isHTTP"],
                                    },
                                    'https': {
                                        'port': 443,
                                        'enabled': discovery["isHTTPS"],
                                    },
                                    'ips': [discovery['ipGeolocations'][0]['ip']]
                                }
                            }
                        }
                    },
                },
                'policy': f5_cs_eap_default_policy,
            }
        }

    def create(self):
        account_id = self.get_account_id()
        catalog_id = self.get_catalog_id()

        if self.want.configuration:
            payload = {
                'account_id': account_id,
                'catalog_id': catalog_id,
                'service_instance_name': self.want.service_instance_name,
                'service_type': 'waf',
                'configuration': self.want.configuration,
            }
            self.create_on_cloud(payload)
        else:
            configuration = self.auto_discover(account_id, catalog_id)
            payload = {
                'account_id': account_id,
                'catalog_id': catalog_id,
                'service_instance_name': self.want.service_instance_name,
                'service_type': 'waf',
                'configuration': configuration,
            }
            self.update_on_cloud(payload, subscription_id=self.have.subscription_id)

        if self.want.activate:
            self.activate()

        return True

    def activate(self):
        state = self.client.activate_subscription(subscription_id=self.have.subscription_id)

        for retry in range(0, 12):
            time.sleep(10)
            state = self.client.get_subscription_status(subscription_id=self.have.subscription_id)
            if state['status'] == 'ACTIVE':
                break

        if state['status'] != 'ACTIVE':
            raise F5ModuleError('cannot activate subscription: ' + state.status)

    def update_current(self):
        self.read_from_cloud(subscription_id=self.want.subscription_id)

        payload = {
            'account_id': self.have.account_id,
            'catalog_id': self.have.catalog_id,
            'service_instance_name': self.have.service_instance_name,
            'service_type': 'waf',
            'configuration': self.changes.configuration,
        }

        if self.want.configuration and self.want.patch is False:
            payload['configuration'] = self.want.configuration
        else:
            if self.changes.configuration.get('details'):
                del self.changes.configuration['details']
            payload['configuration'] = self.changes.configuration

        payload['configuration']['update_comment'] = self.want.update_comment

        self.update_on_cloud(payload, subscription_id=self.want.subscription_id)
        return True

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
            catalog_id=dict(),
            service_instance_name=dict(),
            configuration=dict(type=dict),
            state=dict(
                default='present',
                choices=['present', 'absent', 'fetch']
            ),
            update_comment=dict(default='update EAP application'),
            patch=dict(
                default=False,
                type='bool',
            ),
            activate=dict(
                type='bool',
                default=True,
            ),
        )

        self.argument_spec = {}
        self.argument_spec.update(f5_cs_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module, client=HttpRestApi(HttpConnection()))
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
