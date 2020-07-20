# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

import unittest
from unittest.mock import Mock

from test.units.modules.utils import set_module_args

try:
    from library.modules.f5_cs_eap_ip_enforcement import ModuleParameters
    from library.modules.f5_cs_eap_ip_enforcement import ModuleManager
    from library.modules.f5_cs_eap_ip_enforcement import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_ip_enforcement import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_ip_enforcement import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_ip_enforcement import ArgumentSpec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import CloudservicesApi

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}

hacker_ip = dict(
                    address='192.168.1.2',
                    description='hacker',
                    log=True,
                )

devops_ip = dict(
                    address='192.168.1.3',
                    description='devops',
                    action='allow',
                )


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            subscription_id='s-xxxxxxxxxx',
            action='update',
            ip_enforcement=[
                hacker_ip,
                devops_ip,
            ]

        )

        p = ModuleParameters(params=args)

        assert p.subscription_id == 's-xxxxxxxxxx'
        assert p.action == 'update'

        updated_hacker_ip = p.ip_enforcement[0]
        assert hacker_ip['address'] == updated_hacker_ip['address']
        assert hacker_ip['description'] == updated_hacker_ip['description']
        assert hacker_ip['log'] == updated_hacker_ip['log']
        updated_devops_ip = p.ip_enforcement[1]
        assert devops_ip['address'] == updated_devops_ip['address']
        assert devops_ip['description'] == updated_devops_ip['description']
        assert devops_ip['action'] == updated_devops_ip['action']


class TestIPEnforcementRulesUpdate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_enforcement_list(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'

        ip_enforcement_rules = payload['configuration']['waf_service']['policy']['high_risk_attack_mitigation']['ip_enforcement']['ips']
        updated_hacker_ip = ip_enforcement_rules[0]
        assert hacker_ip['address'] == updated_hacker_ip['address']
        assert hacker_ip['description'] == updated_hacker_ip['description']
        assert updated_hacker_ip['action'] == 'block'
        assert hacker_ip['log'] == updated_hacker_ip['log']
        updated_devops_ip = ip_enforcement_rules[1]
        assert devops_ip['address'] == updated_devops_ip['address']
        assert devops_ip['description'] == updated_devops_ip['description']
        assert devops_ip['action'] == updated_devops_ip['action']
        assert updated_devops_ip['log'] is False

        return load_fixture('f5_cs_eap_ip_enforcement_post_eap_subscription_update.json')

    def test_ip_enforcement_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            action='update',
            ip_enforcement=[
                hacker_ip,
                devops_ip,
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_eap_ip_enforcement_get_eap_subscription.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_enforcement_list)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'

        updated_hacker_ip = results['ip_enforcement'][0]
        assert hacker_ip['address'] == updated_hacker_ip['address']
        assert hacker_ip['description'] == updated_hacker_ip['description']
        assert updated_hacker_ip['action'] == 'block'
        assert hacker_ip['log'] == updated_hacker_ip['log']
        updated_devops_ip = results['ip_enforcement'][1]
        assert devops_ip['address'] == updated_devops_ip['address']
        assert devops_ip['description'] == updated_devops_ip['description']
        assert devops_ip['action'] == updated_devops_ip['action']
        assert updated_devops_ip['log'] is False


class TestIPEnforcementRulesAppend(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_enforcement_list(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'

        ip_enforcement_rules = payload['configuration']['waf_service']['policy']['high_risk_attack_mitigation']['ip_enforcement']['ips']
        bot_ip = ip_enforcement_rules[0]
        assert bot_ip['address'] == '192.168.1.1'
        assert bot_ip['description'] == 'bot_1'
        assert bot_ip['action'] == 'block'
        assert bot_ip['log'] is False
        updated_hacker_ip = ip_enforcement_rules[1]
        assert hacker_ip['address'] == updated_hacker_ip['address']
        assert hacker_ip['description'] == updated_hacker_ip['description']
        assert updated_hacker_ip['action'] == 'block'
        assert hacker_ip['log'] == updated_hacker_ip['log']
        updated_devops_ip = ip_enforcement_rules[2]
        assert devops_ip['address'] == updated_devops_ip['address']
        assert devops_ip['description'] == updated_devops_ip['description']
        assert devops_ip['action'] == updated_devops_ip['action']
        assert updated_devops_ip['log'] is False

        return load_fixture('f5_cs_eap_ip_enforcement_post_eap_subscription_append.json')

    def test_ip_enforcement_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            action='append',
            ip_enforcement=[
                hacker_ip,
                devops_ip,
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_eap_ip_enforcement_get_eap_subscription.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_enforcement_list)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'

        bot_ip = results['ip_enforcement'][0]
        assert bot_ip['address'] == '192.168.1.1'
        assert bot_ip['description'] == 'bot_1'
        assert bot_ip['action'] == 'block'
        assert bot_ip['log'] is False
        updated_hacker_ip = results['ip_enforcement'][1]
        assert hacker_ip['address'] == updated_hacker_ip['address']
        assert hacker_ip['description'] == updated_hacker_ip['description']
        assert updated_hacker_ip['action'] == 'block'
        assert hacker_ip['log'] == updated_hacker_ip['log']
        updated_devops_ip = results['ip_enforcement'][2]
        assert devops_ip['address'] == updated_devops_ip['address']
        assert devops_ip['description'] == updated_devops_ip['description']
        assert devops_ip['action'] == updated_devops_ip['action']
        assert updated_devops_ip['log'] is False


class TestIPEnforcementRulesExclude(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def update_enforcement_list(self, payload, subscription_id, *args, **kwargs):
        assert subscription_id == 's-xxxxxxxxxx'

        ip_enforcement_rules = payload['configuration']['waf_service']['policy']['high_risk_attack_mitigation']['ip_enforcement']['ips']
        bot_ip = ip_enforcement_rules[0]
        assert bot_ip['address'] == '192.168.1.1'
        assert bot_ip['description'] == 'bot_1'
        assert bot_ip['action'] == 'block'
        assert bot_ip['log'] is False

        return load_fixture('f5_cs_eap_ip_enforcement_post_eap_subscription_exclude.json')

    def test_ip_enforcement_update(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            action='exclude',
            ip_enforcement=[
                hacker_ip,
                devops_ip,
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_eap_ip_enforcement_get_eap_subscription.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(side_effect=self.update_enforcement_list)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'

        bot_ip = results['ip_enforcement'][0]
        assert bot_ip['address'] == '192.168.1.1'
        assert bot_ip['description'] == 'bot_1'
        assert bot_ip['action'] == 'block'
        assert bot_ip['log'] is False
