#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from functools import reduce
import OpenSSL.crypto
import datetime

ANSIBLE_METADATA = {'metadata_version': '1.01',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: f5_cs_eap_certificate
short_description: Manage EAP certificate
description: 
    - This module will manage SSL certificate for EAP application
version_added: 1.01
options:
    state:
        description:
            - When C(present) will update or create certificate for EAP
            - When C(absent), will remove certificate or remove assignment 
            - When C(fetch), will read certificate 
        default: present
        choices:
            - present
            - absent
            - fetch
    certificate: 
        description: certificate body
    private_key: 
        description: certificate private key
    passphrase: 
        description: certificate pass phrase
    certificate_id:
        description: previously created certificate id
    subscription_id:
        description: subscription id used for fetch and absent states
    assigned_subscriptions:
        description: list of subscriptions with provided certificate
        - subscription_id:
            description: EAP subscription id
          enabled: 
            description: is HTTPS enabled
          https_port:
            description: https port
          https_redirect: 
            description: redirect traffic from http
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

certificate_id:
    description: id of created or used certificate
assigned_subscriptions:
    description: list of subscriptions where certificated is used
    - subscription_id:
        description: EAP subscription id
      enabled: 
        description: is HTTPS enabled
      https_port:
        description: https port
      https_redirect: 
        description: redirect traffic from http
      update_comment: 
        description: update comment
expiration_date:
    description: certificate expiration date
common_name
    description: certificate common name
subscription_id:
    description: id of used subscription
certificates:
    description: list of available certificates
    - account_id:
        description: account id associated with certificate
      common_name:
        description: certificate common name
      expiration_date:
        description: certificate expiration date
      id:
        description: certificate id

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
        'certificate_id', 'subscription_id', 'assigned_subscriptions', 'expiration_date', 'common_name', 'state',
        'certificates'
    ]

    returnables = [
        'certificate_id', 'subscription_id', 'assigned_subscriptions', 'expiration_date', 'common_name', 'certificates',
        'state'
    ]


class ApiParameters(Parameters):
    @property
    def certificate_id(self):
        return self._values['certificate_id']

    @property
    def assigned_subscriptions(self):
        return self._values['assigned_subscriptions']

    @property
    def expiration_date(self):
        return self._values['expiration_date']

    @property
    def common_name(self):
        return self._values['common_name']

    @property
    def certificates(self):
        return self._values['certificates']


class ModuleParameters(Parameters):
    @property
    def account_id(self):
        return self._values['account_id']

    @property
    def state(self):
        return self._values['state']

    @property
    def certificate_id(self):
        return self._values['certificate_id']

    @property
    def subscription_id(self):
        return self._values['subscription_id']

    @property
    def assigned_subscriptions(self):
        return self._values['assigned_subscriptions']

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

    @property
    def state(self):
        return self.want.state

    @property
    def certificate_id(self):
        return self.have.certificate_id

    @property
    def subscription_id(self):
        return self.want.subscription_id

    @property
    def assigned_subscriptions(self):
        return self.have.assigned_subscriptions

    @property
    def expiration_date(self):
        return self.have.expiration_date

    @property
    def common_name(self):
        return self.have.common_name

    @property
    def certificates(self):
        return self.have.certificates


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
        if self.want.state == "present":
            certificate_id = self.want.certificate_id
            assigned_subscriptions = self.want.assigned_subscriptions
            if certificate_id is None:
                certificate_id = self.find_existing_certificate()
                if certificate_id is None:
                    certificate_id = self.upload_certificate()
                    changed = True
            if assigned_subscriptions:
                for subscription in assigned_subscriptions:
                    params = dict(
                        certificate_id=certificate_id,
                        subscription_id=subscription['subscription_id'],
                        enabled=subscription['enabled'],
                        https_port=subscription['https_port'],
                        https_redirect=subscription['https_redirect'],
                        tls_version=subscription['tls_version'],
                        update_comment=subscription['update_comment'],
                    )
                    changed = self.update_subscription_on_cloud(params)
            self.find_certificate_usage_on_cloud(certificate_id)
        elif self.want.state == "fetch":
            if self.want.certificate_id:
                self.find_certificate_usage_on_cloud(self.want.certificate_id)
            elif self.want.subscription_id:
                certificate_id = self.get_certificate_id_by_subscription_id(self.want.subscription_id)
                if certificate_id:
                    self.find_certificate_usage_on_cloud(certificate_id)
                else:
                    raise F5ModuleError('certificate not found')
            else:
                response = self.get_certificates()
                self.have = ApiParameters(params=dict(certificates=response))
            changed = False
        elif self.want.state == "absent":
            if self.want.certificate_id:
                certificates = self.get_certificates()
                certificate = ([x for x in certificates if x['id'] == self.want.certificate_id] or [None])[0]
                if certificate:
                    self.remove_certificate(self.want.certificate_id)
                    changed = True
            elif self.want.subscription_id:
                certificate = self.get_certificate_id_by_subscription_id(self.want.subscription_id)
                if certificate:
                    self.remove_certificate_from_eap(self.want.subscription_id)
                    changed = True

        self._update_changed_options()

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

    @staticmethod
    def deep_get(dictionary, keys, default=None):
        return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."),
                      dictionary)

    @staticmethod
    def deep_set(dictionary, keys, value):
        current = dictionary
        keys = keys.split(".")
        counter = 1
        for key in keys:
            if counter == len(keys):
                current[key] = value
            else:
                val = current.get(key, None)
                if not isinstance(val, dict):
                    current[key] = dict()
                current = current[key]
                counter += 1

    def change_setting(self, dictionary, path, parameter):
        if self.deep_get(dictionary, path, None) == parameter:
            return False
        else:
            self.deep_set(dictionary, path, parameter)
            return True

    def get_account_id(self):
        if self.want.account_id:
            return self.want.account_id
        current_user = self.client.get_current_user()
        return current_user['primary_account_id']

    def remove_certificate(self, certificate_id):
        self.client.retire_certificate(certificate_id)

    def remove_certificate_from_eap(self, subscription_id):
        subscription = self.client.get_subscription_by_id(subscription_id)
        self.deep_set(subscription, 'configuration.waf_service.application.https.tls.certificate_id', '')
        self.deep_set(subscription, 'configuration.waf_service.application.https.enabled', False)
        self.deep_set(subscription, 'configuration.waf_service.application.http.https_redirect', False)
        del subscription['configuration']['details']
        self.deep_set(subscription, 'configuration.update_comment', 'Remove SSL Certificate')
        self.client.update_subscription(subscription, subscription_id)

    def get_certificates(self):
        account_id = self.get_account_id()
        response = self.client.get_certificates(account_id)
        return response.get('certificates', [])

    def get_subscriptions(self):
        account_id = self.get_account_id()
        response = self.client.get_subscriptions_by_type(subscription_type='waf', account_id=account_id)
        return response.get('subscriptions', [])

    def get_certificate_id_by_subscription_id(self, subscription_id):
        subscription = self.client.get_subscription_by_id(subscription_id)
        return self.deep_get(subscription, 'configuration.waf_service.application.https.tls.certificate_id', None)

    def find_certificate_usage_on_cloud(self, certificate_id):
        certificates = self.get_certificates()
        certificate = ([x for x in certificates if x['id'] == certificate_id] or [dict()])[0]
        subscriptions = self.get_subscriptions()
        assigned_subscriptions = list()
        for subscription in subscriptions:
            if self.deep_get(subscription, 'configuration.waf_service.application.https.tls.certificate_id',
                             None) == certificate_id:
                assigned_subscriptions.append(dict(
                    subscription_id=subscription['subscription_id'],
                    enabled=self.deep_get(subscription, 'configuration.waf_service.application.https.enabled', False),
                    https_port=self.deep_get(subscription, 'configuration.waf_service.application.https.port', 443),
                    https_redirect=self.deep_get(subscription,
                                                 'configuration.waf_service.application.http.https_redirect', False),
                    tls_version=self.deep_get(subscription, 'configuration.waf_service.application.https.tls.version',
                                              '1.2'),
                ))
        self.have = ApiParameters(params=dict(
            certificate_id=certificate_id,
            common_name=certificate.get('common_name', None),
            expiration_date=certificate.get('expiration_date', None),
            assigned_subscriptions=assigned_subscriptions,
        ))

    def update_subscription_on_cloud(self, params):
        subscription = self.client.get_subscription_by_id(subscription_id=params['subscription_id'])
        changed = False
        if params['enabled'] is not None:
            applied = self.change_setting(subscription, 'configuration.waf_service.application.https.enabled',
                                          params['enabled'])
            changed = changed or applied
        if params['https_port'] is not None:
            applied = self.change_setting(subscription, 'configuration.waf_service.application.https.port',
                                          params['https_port'])
            changed = changed or applied
        if params['https_redirect'] is not None:
            applied = self.change_setting(subscription, 'configuration.waf_service.application.http.https_redirect',
                                          params['https_redirect'])
            changed = changed or applied
        if params['tls_version'] is not None:
            applied = self.change_setting(subscription, 'configuration.waf_service.application.https.tls.version',
                                          params['tls_version'])
            changed = changed or applied
        if params['certificate_id'] is not None:
            applied = self.change_setting(subscription,
                                          'configuration.waf_service.application.https.tls.certificate_id',
                                          params['certificate_id'])
            changed = changed or applied
        else:
            applied = self.change_setting(subscription,
                                          'configuration.waf_service.application.https.tls.certificate_id', '')
            changed = changed or applied
        if changed is True:
            del subscription['configuration']['details']
            subscription['configuration']['update_comment'] = params['update_comment']
            self.client.update_subscription(subscription, params['subscription_id'])
        return changed

    def find_existing_certificate(self):
        try:
            cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM,
                self.want.certificate.encode('utf-8'))
            date = cert.get_notAfter()
            name = cert.get_subject()
            provided_exp_date = datetime.datetime.strptime(date.decode('utf-8'), '%Y%m%d%H%M%SZ')
            provided_common_name = name.commonName

            certificates = self.get_certificates()
            certificate = \
            ([x for x in certificates if datetime.datetime.strptime(x['expiration_date'], '%Y-%m-%dT%H:%M:%SZ') ==
              provided_exp_date and x['common_name'] == provided_common_name][:1] or [dict()])[0]
            return certificate.get('id', None)
        except:
            return None

    def upload_certificate(self):
        account_id = self.get_account_id()

        certificate_payload = dict(
            certificate=self.want.certificate,
            private_key=self.want.private_key,
            passphrase=self.want.passphrase,
            certificate_chain=self.want.certificate_chain,
            account_id=account_id
        )

        cert_response = self.client.post_certificate(payload=certificate_payload)
        return cert_response['id']


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False

        subscription_spec = dict(
            subscription_id=dict(required=True),
            enabled=dict(required=False, type='bool', default=True),
            https_port=dict(required=False, type='int', default=443),
            https_redirect=dict(required=False, type='bool', default=True),
            tls_version=dict(required=False, default='1.2'),
            update_comment=dict(required=False, default='Update EAP certificate'),
        )

        argument_spec = dict(
            state=dict(required=False, default='present'),
            account_id=dict(required=False, default=None),
            subscription_id=dict(required=False, default=None),
            certificate_id=dict(required=False, default=None),
            certificate=dict(required=False, no_log=True),
            private_key=dict(required=False, no_log=True),
            passphrase=dict(required=False, no_log=True, default=''),
            certificate_chain=dict(required=False, no_log=True, default=''),
            assigned_subscriptions=dict(required=False, type='list', elements='dict', options=subscription_spec),
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
