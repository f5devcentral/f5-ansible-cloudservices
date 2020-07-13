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
    from library.modules.f5_cs_eap_cname_fetch import ModuleParameters
    from library.modules.f5_cs_eap_cname_fetch import ModuleManager
    from library.modules.f5_cs_eap_cname_fetch import ArgumentSpec
    from library.module_utils.cloudservices import HttpRestApi
    from library.module_utils.cloudservices import HttpConnection
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_cname_fetch import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_cname_fetch import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_eap_cname_fetch import ArgumentSpec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import HttpRestApi
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import HttpConnection


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
            f5_cloudservices=dict(
                user='user',
                password='password',
            )
        )

        p = ModuleParameters(params=args)

        assert p.subscription_id == 's-xxxxxxxxxx'
        assert p.f5_cloudservices['user'] == 'user'
        assert p.f5_cloudservices['password'] == 'password'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_cname_fetch(self, *args):
        set_module_args(dict(
            subscription_id='s-xxxxxxxxxx',
            f5_cloudservices=dict(
                user='user',
                password='password',
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        api_client = HttpRestApi(HttpConnection())
        api_client.login = Mock()
        fixture = load_fixture('f5_cs_eap_cname_fetch_get_eap_subscription.json')
        api_client.get_subscription_by_id = Mock(return_value=fixture)

        mm = ModuleManager(module=module, client=api_client)
        mm.exists = Mock(return_value=False)
        mm.publish_on_device = Mock(return_value=True)
        mm.draft_exists = Mock(return_value=False)
        mm._create_existing_policy_draft_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['CNAMEValue'] == 'waf-xxxxxxxxxx.waf.prd.f5aas.com'
        assert results['subscription_id'] == 's-xxxxxxxxxx'

