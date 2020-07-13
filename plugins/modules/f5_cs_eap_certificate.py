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
module: f5_cs_eap_certificate
short_description: Apply EAP certificate
description: 
    - This module will apply and enable SSL certificate for EAP application
version_added: 1.0
options:
    subscription_id:
        description: ID of existing subscription
    account_id:
        description: ID of your main user’s primary account (where you will create instances)
    enabled:
        description: Enable https protocol if True
    certificate:
        description: Certificate body
    private_key:
        description: Private key for certificate
    passphrase:
        description: Certificate pass phrase
    certificate_chain:
        description: Certificate chain
    https_port:
        description: https port
        default: 443
    https_redirect:
        description: Auto redirect from http to https
    update_comment:
        description: update comment
author:
  - Alex Shemyakin
'''


EXAMPLES = '''
description: 
    - The examples can be found in /examples/f5_cs_eap_certificate.yml
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
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import AnsibleF5Parameters


class Parameters(AnsibleF5Parameters):
    updatables = [
        'subscription_id', 'account_id', 'configuration'
    ]

    returnables = [
        'subscription_id', 'configuration', 'account_id', 'service_instance_name'
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
        return self._values['account_id']

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
    def account_id(self):
        return self._values['account_id']

    @property
    def enabled(self):
        return self._values['enabled']

    @property
    def certificate(self):
        return self._values['certificate']

    @property
    def private_key(self):
        return self._values['private_key']

    @property
    def passphrase(self):
        return self._values['passphrase']

    @property
    def certificate_chain(self):
        return self._values['certificate_chain']

    @property
    def https_port(self):
        return self._values['https_port']

    @property
    def https_redirect(self):
        return self._values['https_redirect']

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
        return self.have.configuration

    @property
    def subscription_id(self):
        return self.have.subscription_id

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

        certificate_id = self.upload_certificate()
        configuration = self.changes.configuration

        configuration['waf_service']['application']['https'] = {
            'enabled': self.want.enabled,
            'port': self.want.https_port,
            'tls': {
                'certificate_id': certificate_id
            }
        }
        configuration['waf_service']['application']['https']['https_redirect'] = self.want.https_redirect

        payload = {
            'account_id': self.have.account_id,
            'catalog_id': self.have.catalog_id,
            'service_instance_name': self.have.service_instance_name,
            'service_type': 'waf',
            'configuration': self.changes.configuration,
        }

        self.update_on_cloud(payload, subscription_id=self.want.subscription_id)
        return True

    def upload_certificate(self):
        certificate_payload = dict(
            account_id=self.have.account_id,
            certificate=self.want.certificate,
            private_key=self.want.private_key,
            passphrase=self.want.passphrase,
            certificate_chain=self.want.certificate_chain,
        )

        cert_response = self.client.post_certificate(payload=certificate_payload)
        return cert_response['id']

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
            enabled=dict(required=False, type='bool', default=True),
            certificate=dict(required=True, no_log=True),
            private_key=dict(required=True, no_log=True),
            passphrase=dict(required=False, no_log=True, default=''),
            certificate_chain=dict(required=False, no_log=True, default=''),
            https_port=dict(required=False, type='int', default=443),
            https_redirect=dict(required=False, type='bool', default=True),
            update_comment=dict(required=False, default='Update EAP certificate'),
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
