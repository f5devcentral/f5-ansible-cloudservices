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
    from library.modules.f5_cs_users import ModuleParameters
    from library.modules.f5_cs_users import ModuleManager
    from library.modules.f5_cs_users import ArgumentSpec
    from library.module_utils.cloudservices import CloudservicesApi
except ImportError:
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_users import ModuleParameters
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_users import ModuleManager
    from ansible_collections.f5devcentral.cloudservices.plugins.modules.f5_cs_users import ArgumentSpec
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
            users=[dict(
                email='email@email.email'
            )],
            state='absent',
        )

        p = ModuleParameters(params=args)

        assert p.account_id == 'a-xxxxxxxxxx'
        assert p.state == 'absent'
        assert len(p.users) == 1


class TestOrganizationOperate(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        get_user_fake = load_fixture('f5_cs_subscription_app_get_user.json')
        get_memberships_fake = load_fixture('f5_cs_get_memberships.json')
        get_account_fake = load_fixture('f5_cs_organization_get_account.json')
        connection = Mock()
        self.api_client = CloudservicesApi(connection)
        self.api_client.login = Mock()

        self.api_client.get_current_user = Mock(return_value=get_user_fake)
        self.api_client.get_memberships = Mock(return_value=get_memberships_fake)
        self.api_client.get_account = Mock(return_value=get_account_fake)

        list_account_members_fake = load_fixture('f5_cs_list_account_members.json')
        self.api_client.list_account_members = Mock(return_value=list_account_members_fake)

        list_invites_fake = load_fixture('f5_cs_list_invites.json')
        self.api_client.list_invites = Mock(return_value=list_invites_fake)

        self.api_client.delete_invite = Mock(return_value=dict())
        self.api_client.delete_account_member = Mock(return_value=dict())
        self.api_client.create_invite_into_account = Mock(return_value=dict())

    def test_user_invite(self, *args):
        set_module_args(dict(
            state='present',
            users=[
                dict(
                    email='testemail@email.email',
                    role_name='privileged-user',
                )
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        users = results['users']
        assert len(users) == 2

    def test_users_fetch(self, *args):
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
        users = results['users']
        assert len(users) == 2

    def test_remove_user(self, *args):
        set_module_args(dict(
            state='absent',
            users=[
                dict(email='email@email.email')
            ]
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        mm = ModuleManager(module=module, client=self.api_client)
        results = mm.exec_module()

        assert results['changed'] is True
        users = results['users']
        assert len(users) == 2
