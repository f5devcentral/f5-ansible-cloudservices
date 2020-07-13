#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: f5_cs_eap_ip_enforcement
short_description: Update IP Enforcement Rules
description: 
    - This module will add, remove and update Essential App Protect IP Enforcement Rules list
version_added: 1.0
options:
    subscription_id:
        description: ID of existing subscription
    ip_enforcement:
        - address:
            description: IP address
            required: True
          description:
            description: Rule description
            default:             
          action:
            description: Block or Allow
            default: block
          log:
            description: Log requests
            default: False
    account_id:
        description:
            - ID of your main user’s primary account (where you will create instances)
    action:
        description:
            - When C(append), will append provided list to the EAP application
            - When C(absent), will exclude provided IPs from the EAP application
            - When C(update) will replace EAP application Rules list with provided
        default: update
        choices:
            - append
            - exclude
            - update
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: 
    - The examples can be found in /examples/f5_cs_eap_ip_enforcement.yml
'''

RETURN = r'''
subscription_id
    description: ID of the changed EAP application
    sample: s-xxxxxxxxxx
ip_enforcement:
    - address:
        description: IP address
        required: True   
        sample: 192.168.1.1
      description:
        description: Rule description
        default:             
        sample: dev ops
      action:
        description: Block or Allow
        default: block
        sample: allow
      log:
        description: Log requests
        default: False
        sample: false
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
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import AnsibleF5Parameters


class Parameters(AnsibleF5Parameters):
    updatables = [
        'subscription_id', 'ip_enforcement', 'configuration'
    ]

    returnables = [
        'subscription_id', 'ip_enforcement'
    ]


class ApiParameters(Parameters):
    @property
    def ip_enforcement(self):
        return self._values['configuration']['waf_service']['policy']['high_risk_attack_mitigation']['ip_enforcement']['ips']

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
    def ip_enforcement(self):
        return self._values['ip_enforcement']

    @property
    def action(self):
        return self._values['action']

    @property
    def update_comment(self):
        return self._values['update_comment']


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

    @property
    def configuration(self):
        config = self.have.configuration
        w_ips = self.want.ip_enforcement
        h_ips = self.have.ip_enforcement
        ip_list = list()
        if self.want.action == 'update':
            ip_list = list({ip['address']: ip for ip in w_ips}.values())
        elif self.want.action == 'append':
            ips = h_ips + w_ips
            ip_list = list({ip['address']: ip for ip in ips}.values())
        elif self.want.action == 'exclude':
            unique_ips = {ip['address']: ip for ip in h_ips}
            for ip in w_ips:
                if ip['address'] in unique_ips:
                    del unique_ips[ip['address']]
            ip_list = list(unique_ips.values())

        config['waf_service']['policy']['high_risk_attack_mitigation']['ip_enforcement']['ips'] = ip_list
        return config

    @property
    def subscription_id(self):
        return self.have.subscription_id

    @property
    def ip_enforcement(self):
        return self.have.ip_enforcement


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
        self.read_from_cloud()

        self.changes.configuration['update_comment'] = self.want.update_comment
        if self.changes.configuration.get('details'):
            del self.changes.configuration['details']

        payload = {
            'account_id': self.have.account_id,
            'catalog_id': self.have.catalog_id,
            'service_instance_name': self.have.service_instance_name,
            'service_type': 'waf',
            'configuration': self.changes.configuration,
        }

        self.update_on_cloud(payload, subscription_id=self.want.subscription_id)
        return True

    def read_from_cloud(self):
        subscription = self.client.get_subscription_by_id(subscription_id=self.want.subscription_id)
        self.have = ApiParameters(params=subscription)
        self._update_changed_options()

    def update_on_cloud(self, payload, subscription_id):
        self.have = ApiParameters(params=self.client.update_subscription(payload, subscription_id))
        self._update_changed_options()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False

        ip_enforcement_spec = {
            'address': dict(
                required=True,
            ),
            'description': dict(
                default='',
            ),
            'action': dict(
                default='block',
            ),
            'log': dict(
                type='bool',
                default=False
            )
        }

        argument_spec = dict(
            subscription_id=dict(required=True),
            update_comment=dict(default='Update IP Enforcement Rules'),
            ip_enforcement=dict(type='list', elements='dict', options=ip_enforcement_spec),
            action=dict(
                default='update',
                choices=['update', 'append', 'exclude']
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
