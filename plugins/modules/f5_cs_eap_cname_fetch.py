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
module: f5_cs_eap_cname_fetch.py
short_description: Get CNAMEValue
description: 
    - This module will return CNAME record for Essential App Protect application 
version_added: 1.0
options:
    subscription_id:
        description:
            - ID of existing subscription
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: 
    - The examples can be found in /examples/f5_cs_eap_cname_fetch.yml
'''

RETURN = r'''
subscription_id
    description: ID of the EAP application
    sample: s-xxxxxxxxxx
CNAMEValue
    description: CNAME record 
    sample: waf-xxxxxxxxx.waf.prd.f5aas.com
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
        'subscription_id', 'CNAMEValue'
    ]

    returnables = [
        'subscription_id', 'CNAMEValue'
    ]


class ApiParameters(Parameters):
    @property
    def CNAMEValue(self):
        return self._values['configuration']['details']['CNAMEValue']


class ModuleParameters(Parameters):
    @property
    def subscription_id(self):
        if self._values['subscription_id'] is None:
            return None
        return self._values['subscription_id']


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
    def subscription_id(self):
        return self.have.subscription_id

    @property
    def CNAMEValue(self):
        return self.have.CNAMEValue


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
        changed = False
        result = dict()

        self.read_from_cloud()

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

    def read_from_cloud(self):
        subscription = self.client.get_subscription_by_id(subscription_id=self.want.subscription_id)
        self.have = ApiParameters(params=subscription)
        self._update_changed_options()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False
        argument_spec = dict(
            subscription_id=dict(),
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
