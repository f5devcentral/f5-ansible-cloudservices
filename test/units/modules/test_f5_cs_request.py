# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

import unittest
from unittest.mock import Mock

from test.units.modules.utils import set_module_args

try:
    from library.modules.f5_cs_request import ModuleParameters
    from library.modules.f5_cs_request import ModuleManager
    from library.modules.f5_cs_request import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_request import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_request import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_request import ArgumentSpec
    from ansible_collections.f5devcentral.cloudservices.plugins.module_utils.cloudservices import CloudservicesApi


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            account_id='a-xxxxxxxxxx',
            body={
                "test_key": "test_value"
            },
            method='POST',
            url='/v1/api',
        )

        p = ModuleParameters(params=args)

        assert p.account_id == 'a-xxxxxxxxxx'
        assert p.body['test_key'] == 'test_value'
        assert p.method == 'POST'
        assert p.url == '/v1/api'


class TestOrganizationOperate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def send_request(self, url, method=None, **kwargs):
        assert url == '/v1/api'
        body = kwargs.pop('data', None)
        assert body["test_key"] == "test_value"
        assert method == "POST"
        headers = kwargs.pop('headers', None)
        assert headers["Content-Type"] == "application/json"
        assert headers["X-F5aaS-Preferred-Account-Id"] == "a-xxxxxxxxxx"
        return dict(code=200, contents=dict(resp="test"))

    def test_organization_create(self, *args):
        set_module_args(dict(
            account_id='a-xxxxxxxxxx',
            body={
                "test_key": "test_value"
            },
            method='POST',
            url='/v1/api',
        ))

        connection = Mock()
        connection.send_request = Mock(side_effect=self.send_request)
        api_client = CloudservicesApi(connection)
        api_client.login = Mock()

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=api_client)
        results = mm.exec_module()

        assert results['changed'] is False
        assert results['code'] == 200
        assert results['contents']["resp"] == "test"
