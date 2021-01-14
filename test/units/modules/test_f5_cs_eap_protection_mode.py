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
    from library.modules.f5_cs_eap_protection_mode import ModuleParameters
    from library.modules.f5_cs_eap_protection_mode import ModuleManager
    from library.modules.f5_cs_eap_protection_mode import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_protection_mode import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_protection_mode import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_protection_mode import ArgumentSpec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import CloudservicesApi


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


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
            hi_risk_attack=dict(
                enabled=True,
                enforcement_mode='monitoring'
            ),
            threat_campaign=dict(
                enabled=True,
                enforcement_mode='monitoring'
            ),
            malicious_ip=dict(
                enabled=True,
                enforcement_mode='monitoring'
            ),
            update_comment='update EAP protection mode'
        )

        p = ModuleParameters(params=args)

        assert p.subscription_id == 's-xxxxxxxxxx'
        assert p.hi_risk_attack['enabled'] is True
        assert p.hi_risk_attack['enforcement_mode'] == 'monitoring'
        assert p.threat_campaign['enabled'] is True
        assert p.threat_campaign['enforcement_mode'] == 'monitoring'
        assert p.malicious_ip['enabled'] is True
        assert p.malicious_ip['enforcement_mode'] == 'monitoring'
        assert p.update_comment == 'update EAP protection mode'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_protection_change(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            hi_risk_attack=dict(
                enabled=True,
                enforcement_mode='monitoring'
            ),
            threat_campaign=dict(
                enabled=True,
                enforcement_mode='monitoring'
            ),
            malicious_ip=dict(
                enabled=True,
                enforcement_mode='monitoring'
            ),
            update_comment='update EAP protection mode'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        get_subscription_fake = load_fixture('f5_cs_eap_protection_mode_get_subscription.json')
        update_subscription_fake = load_fixture('f5_cs_eap_protection_mode_update_subscription.json')

        connection = Mock()
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()
        api_client.get_subscription_by_id = Mock(return_value=get_subscription_fake)
        api_client.update_subscription = Mock(return_value=update_subscription_fake)

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['subscription_id'] == 's-xxxxxxxxxx'
        assert results['hi_risk_attack']['enabled'] is True
        assert results['hi_risk_attack']['enforcement_mode'] == 'monitoring'
        assert results['malicious_ip']['enabled'] is True
        assert results['malicious_ip']['enforcement_mode'] == 'monitoring'
        assert results['threat_campaign']['enabled'] is True
        assert results['threat_campaign']['enforcement_mode'] == 'monitoring'
