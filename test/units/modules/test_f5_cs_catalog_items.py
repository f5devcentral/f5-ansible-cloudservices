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
    from library.modules.f5_cs_catalog_items import ModuleParameters
    from library.modules.f5_cs_catalog_items import ModuleManager
    from library.modules.f5_cs_catalog_items import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_catalog_items import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_catalog_items import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_catalog_items import ArgumentSpec
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
            account_id='a-xxxxxxxxxx',
            catalog_id='c-xxxxxxxxxx',
            service='secondary_dns',
            state='absent',
        )

        p = ModuleParameters(params=args)

        assert p.account_id == 'a-xxxxxxxxxx'
        assert p.catalog_id == 'c-xxxxxxxxxx'
        assert p.service == 'secondary_dns'
        assert p.state == 'absent'


class TestOrganizationOperate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        get_user_fake = load_fixture('f5_cs_subscription_app_get_user.json')
        enable_catalog_item_fake = load_fixture('f5_cs_get_memberships.json')
        get_account_fake = load_fixture('f5_cs_organization_get_account.json')
        connection = Mock()
        self.api_client = CloudservicesApi(connection)
        self.api_client.login = Mock()

        self.api_client.enable_catalog_item = Mock(return_value=enable_catalog_item_fake)
        self.api_client.get_current_user = Mock(return_value=get_user_fake)
        self.api_client.disable_catalog_item = Mock(return_value=dict())
        self.api_client.get_account = Mock(return_value=get_account_fake)

    def test_subscribe(self, *args):
        set_module_args(dict(
            account_id='a-xxxxxxxxxx',
            catalog_id='c-aaxBJkfg8u',
            state='present',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        assert results['account_id'] == 'a-xxxxxxxxxx'
        assert results['catalog_id'] == 'c-aaxBJkfg8u'

    def test_unsubscribe(self, *args):
        set_module_args(dict(
            account_id='a-xxxxxxxxxx',
            catalog_id='c-aaxBJkfg8u',
            state='absent',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['account_id'] == 'a-xxxxxxxxxx'
        assert results['catalog_id'] == 'c-aaxBJkfg8u'

    def test_fetch_all(self, *args):
        set_module_args(dict(
            state='fetch',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        catalog_items = results['catalog_items']
        assert len(catalog_items) == 1

    def test_fetch(self, *args):
        set_module_args(dict(
            state='fetch',
            account_id='a-xxxxxxxxxx',
            catalog_id='c-aaxBJkfg8u',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        assert results['account_id'] == 'a-xxxxxxxxxx'
        assert results['catalog_id'] == 'c-aaxBJkfg8u'
        assert results['status'] == 'SUBSCRIBED'
        assert results['service'] == 'secondary_dns'
