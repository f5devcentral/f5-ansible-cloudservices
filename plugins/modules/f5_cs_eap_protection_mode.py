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
module: f5_cs_eap_protection_mode
short_description: Update EAP Protection mode
description: This module will manage protection settings for EAP Application
version_added: 1.0
options:
    subscription_id:
        description: ID of existing subscription
    hi_risk_attack:
        description: High-risk Attack configuration
        enabled:
            description: Turn on High-risk Attack Mitigation
            default: True
        enforcement_mode:
            description: protection mode
            default: "blocking"
            choices:
                - blocking
                - monitoring
    malicious_ip:
        description: Malicious IP enforcement configuration
        enabled:
            description: Turn on Malicious IP enforcement
            default: True
        enforcement_mode:
            description: protection mode
            default: "blocking"
            choices:
                - blocking
                - monitoring
    threat_campaign:
        description: Threat Campaign configuration
        enabled:
            description: Turn on Threat Campaign enforcement
            default: True
        enforcement_mode:
            description: protection mode
            default: "blocking"
            choices:
                - blocking
                - monitoring
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: The examples can be found in /examples/f5_cs_eap_protection_mode.yml
'''

RETURN = r'''
subscription_id:
    description: ID of the changed EAP application
    sample: s-xxxxxxxxxx
hi_risk_attack:
    description: High-risk Attack configuration
    type: complex
    contains:
        enabled:
            description: High-risk Attack Mitigation state
            default: True
        mode:
            description: protection mode
            default: "blocking"
            choices:
                - blocking
                - monitoring
malicious_ip:
    description: Malicious IP enforcement configuration
    type: complex
    contains:
        enabled:
            description: Malicious IP enforcement state
            default: True
        mode:
            description: protection mode
            default: "blocking"
            choices:
                - blocking
                - monitoring
threat_campaign:
    description: Threat Campaign configuration
    type: complex
    contains:
        enabled:
            description: Threat Campaign enforcement state
            default: True
        mode:
            description: protection mode
            default: "blocking"
            choices:
                - blocking
                - monitoring
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
        'configuration', 'account_id', 'subscription_id', 'hi_risk_attack', 'threat_campaign', 'malicious_ip'
    ]

    returnables = [
        'subscription_id', 'hi_risk_attack', 'threat_campaign', 'malicious_ip'
    ]


class ApiParameters(Parameters):
    @property
    def hi_risk_attack(self):
        return dict(
            enabled=self._values['configuration']['waf_service']['policy']['high_risk_attack_mitigation']['enabled'],
            enforcement_mode=self._values['configuration']['waf_service']['policy']['high_risk_attack_mitigation'][
                'enforcement_mode']
        )

    @property
    def threat_campaign(self):
        return dict(
            enabled=self._values['configuration']['waf_service']['policy']['threat_campaigns']['enabled'],
            enforcement_mode=self._values['configuration']['waf_service']['policy']['threat_campaigns'][
                'enforcement_mode']
        )

    @property
    def malicious_ip(self):
        return dict(
            enabled=self._values['configuration']['waf_service']['policy']['malicious_ip_enforcement']['enabled'],
            enforcement_mode=self._values['configuration']['waf_service']['policy']['malicious_ip_enforcement'][
                'enforcement_mode']
        )

    @property
    def configuration(self):
        if self._values['configuration'] is None:
            return None
        return self._values['configuration']


class ModuleParameters(Parameters):
    @property
    def subscription_id(self):
        if self._values['subscription_id'] is None:
            return None
        return self._values['subscription_id']

    @property
    def hi_risk_attack(self):
        return self._values['hi_risk_attack']

    @property
    def threat_campaign(self):
        return self._values['threat_campaign']

    @property
    def malicious_ip(self):
        return self._values['malicious_ip']

    @property
    def update_comment(self):
        return self._values['update_comment']

    @property
    def configuration(self):
        if self._values['configuration'] is None:
            return None
        return self._values['configuration']


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

    @property
    def configuration(self):
        if self._values['configuration'] is None:
            return None
        return self._values['configuration']


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

    @property
    def configuration(self):
        config = self.have.configuration
        if self.want.hi_risk_attack:
            if self.want.hi_risk_attack['enabled'] is not None:
                config['waf_service']['policy']['high_risk_attack_mitigation']['enabled'] = self.want.hi_risk_attack['enabled']
            if self.want.hi_risk_attack['enforcement_mode']:
                config['waf_service']['policy']['high_risk_attack_mitigation']['enforcement_mode'] = self.want.hi_risk_attack['enforcement_mode']
        if self.want.threat_campaign:
            if self.want.threat_campaign['enabled'] is not None:
                config['waf_service']['policy']['threat_campaigns']['enabled'] = self.want.threat_campaign['enabled']
            if self.want.threat_campaign['enforcement_mode']:
                config['waf_service']['policy']['threat_campaigns']['enforcement_mode'] = self.want.threat_campaign['enforcement_mode']
        if self.want.malicious_ip:
            if self.want.malicious_ip['enabled'] is not None:
                config['waf_service']['policy']['malicious_ip_enforcement']['enabled'] = self.want.malicious_ip['enabled']
            if self.want.malicious_ip['enforcement_mode']:
                config['waf_service']['policy']['malicious_ip_enforcement']['enforcement_mode'] = self.want.malicious_ip['enforcement_mode']
        return config

    @property
    def subscription_id(self):
        return self.have.subscription_id

    @property
    def hi_risk_attack(self):
        return self.have.hi_risk_attack

    @property
    def malicious_ip(self):
        return self.have.malicious_ip

    @property
    def threat_campaign(self):
        return self.have.threat_campaign

    @property
    def account_id(self):
        return self.have.account_id


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

        argument_spec = dict(
            subscription_id=dict(required=True),
            update_comment=dict(default='Update IP Enforcement Rules'),
            hi_risk_attack=dict(
                type=dict,
                enabled=dict(type='bool', default=None),
                enforcement_mode=dict(default=None)
            ),
            threat_campaign=dict(
                type=dict,
                enabled=dict(type='bool', default=None),
                enforcement_mode=dict(default=None)
            ),
            malicious_ip=dict(
                type=dict,
                enabled=dict(type='bool', default=None),
                enforcement_mode=dict(default=None)
            )
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
