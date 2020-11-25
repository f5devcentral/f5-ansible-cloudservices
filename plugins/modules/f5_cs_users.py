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
module: f5_cs_users
short_description: Manage F5 CS Organization Users
description: 
    - This module will manage Users and Invites 
version_added: 1.0
options:
    state:
        description:
            - When C(present), will invite, create or update existing user
            - When C(absent), will remove user
            - When C(fetch), will fetch all available users for account
        default: present
        choices:
            - present
            - absent
            - fetch
    users:
        description: list of users to create or update
        user_id:
            description: user id
        invite_id:
            description: invite id
        email: 
            description: user email
        first_name: 
            description: user first name
        last_name: 
            description: user last name
        role_id:
            description: role id
        role_name: 
            description: user role
            choices:
             - privileged-user
             - limited-user
             - owner
author:
  - Alex Shemyakin
'''

EXAMPLES = '''
description: 
    - The examples can be found in /examples/f5_cs_users.yml
'''

RETURN = r'''
account_id:
    description: is of associated account
users:
    description: list of users and invites
    user_id:
        description: user id
    invite_id:
        description: invite id
    email: 
        description: user email
    first_name: 
        description: user first name
    last_name: 
        description: user last name
    role_id:
        description: user role id
    role_name: 
        description: user role
    status:
        description: invite status
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
        'account_id',
        'users'
    ]

    returnables = [
        'account_id',
        'users'
    ]


class ApiParameters(Parameters):
    @property
    def account_id(self):
        return self._values['account_id']

    @property
    def users(self):
        if self._values['users'] is None:
            return []
        return self._values['users']


class ModuleParameters(Parameters):
    @property
    def account_id(self):
        return self._values['account_id']

    @property
    def users(self):
        if self._values['users'] is None:
            return []
        return self._values['users']

    @property
    def state(self):
        return self._values['state']


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

    def _diff_complex_items(self, want, have):
        if want == [] and have is None:
            return None
        if want is None and have:
            return have
        w = self.to_tuple(want)
        h = self.to_tuple(have)
        if set(w).issubset(set(h)):
            return None
        else:
            return want

    @property
    def users(self):
        return self.have.users

    @property
    def account_id(self):
        if self.have.account_id:
            return self.have.account_id
        return self.want.account_id


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = kwargs.pop('client')
        self.want = ModuleParameters(params=self.module.params, client=self.client)
        self.have = ApiParameters(client=self.client)
        self.changes = UsableChanges()
        if self.want.account_id:
            self.client.account_id = self.want.account_id

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
        state = self.want.state

        if state == 'present':
            changed = self.present()
        elif state == 'fetch':
            self.read_from_cloud()
        elif state == 'absent':
            changed = self.absent()

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

    def get_account_id(self):
        if self.want.account_id:
            return self.want.account_id
        current_user = self.client.get_current_user()
        return current_user['primary_account_id']

    def get_users(self, account_id):
        response = self.client.list_account_members(account_id)
        return response.get('users', [])

    def get_invites(self):
        response = self.client.list_invites()
        return response.get('invites', [])

    def exists(self, w_user):
        cloud_users = self.read_from_cloud()['users']
        user = None
        for c_user in cloud_users:
            if (w_user.get('user_id', None) and w_user['user_id'].lower() == c_user['user_id']) \
                    or (w_user.get('email', None) and w_user['email'].lower() == c_user['email']) \
                    or (w_user.get('invite_id', None) and w_user['invite_id'] == c_user.get('invite_id', None)):
                user = c_user
                break
        return user

    def present(self):
        changed = False
        for w_user in self.want.users:
            h_user = self.exists(w_user)
            w_role_id = w_user.get('role_id', None) or self.get_role_id_by_name(w_user['role_name'])
            if h_user is not None:
                if h_user.get('role_id', None) != w_role_id and h_user.get('user_id', None):
                    self.update_on_cloud(h_user['user_id'], w_role_id)
                    changed = True
                if h_user.get('role_id', None) != w_role_id and h_user.get('invite_id', None):
                    self.resend_invite(h_user['invite_id'], h_user, w_role_id)
                    changed = True
            else:
                self.send_invite(w_user, w_role_id)
                changed = True

        if changed is True:
            self.read_from_cloud()

        return changed

    def update_on_cloud(self, user_id, role_id):
        account_id = self.get_account_id()
        payload = {
            'account_id': account_id,
            'user_id': user_id,
            'role_id': role_id,
        }
        self.client.update_account_member(payload, account_id, user_id)

    def resend_invite(self, invite_id, user, role_id):
        self.client.delete_invite(invite_id)
        self.send_invite(user, role_id)

    def send_invite(self, user, role_id):
        account_id = self.get_account_id()
        payload = {
            'inviter_account_id': account_id,
            'account_ids': [account_id],
            'invitees': [
                {
                    'first_name': user.get('first_name', ''),
                    'last_name': user.get('last_name', ''),
                    'email': user.get('email', ''),
                }
            ],
            'role_id': role_id,
            'cascade': "CASCADE_UPWARD"
        }
        self.client.create_invite_into_account(payload)

    def read_from_cloud(self):
        account_id = self.get_account_id()
        users = self.get_users(account_id)
        invites = list(filter(lambda i: i['inviter_account_id'] == account_id, self.get_invites()))

        result = {
            'users': [],
            'account_id': account_id,
        }

        existing_users = {}

        for user in users:
            result['users'].append(dict(
                user_id=user['user_id'],
                first_name=user['user'].get('first_name', ''),
                last_name=user['user'].get('last_name', ''),
                email=user['user']['email'],
                role_id=user['role_id'],
                role_name=user['role_name'],
            ))
            existing_users[user['user']['email']] = user['user_id']

        for user in invites:
            if existing_users.get(user['invitee_email'], False) is False \
                    and user['status'] != 'accepted':
                result['users'].append(dict(
                    invite_id=user['invite_id'],
                    first_name=user['first_name'],
                    last_name=user['last_name'],
                    email=user['invitee_email'],
                    status=user['status'],
                    role_id=user['role_id'],
                    role_name=self.get_role_name_by_id(user['role_id']),
                ))

        self.have = ApiParameters(params=result)
        self._update_changed_options()
        return result

    @staticmethod
    def get_roles():
        return [
            {
                "id": "r-rTLKOYBmg",
                "name": "owner",
                "description": ""
            },
            {
                "id": "r-G0LKdYfiR",
                "name": "privileged-user",
                "description": ""
            },
            {
                "id": "r-NAYFdYfiR",
                "name": "limited-user",
                "description": ""
            }
        ]

    def get_role_id_by_name(self, name):
        roles = self.get_roles()
        role = ([x for x in roles if x['name'] == name] or [None])[0]
        if role is None:
            raise F5ModuleError('role not found')
        return role['id']

    def get_role_name_by_id(self, role_id):
        roles = self.get_roles()
        role = ([x for x in roles if x['id'] == role_id] or [None])[0]
        if role is None:
            return 'unknown'
        return role['name']

    def absent(self):
        changed = False
        for w_user in self.want.users:
            h_user = self.exists(w_user)
            if h_user is not None:
                if h_user.get('user_id', None) is not None:
                    self.client.delete_account_member(self.have.account_id, h_user['user_id'])
                    changed = True
                if h_user.get('invite_id', None) is not None:
                    self.client.delete_invite(h_user['invite_id'])
                    changed = True

        if changed is True:
            self.read_from_cloud()

        return changed


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False

        user_spec = {
            'user_id': dict(
                default=None,
            ),
            'invite_id': dict(
                default=None,
            ),
            'role_id': dict(
                default=None,
            ),
            'role_name': dict(
                default=None,
                choices=['owner', 'privileged-user', 'limited-user']
            ),
            'first_name': dict(
                default=None,
            ),
            'last_name': dict(
                default=None,
            ),
            'email': dict(
                default=None,
            ),
            'status': dict(
                default=None,
            ),
        }

        argument_spec = dict(
            account_id=dict(default=None),
            users=dict(type='list', elements='dict', options=user_spec, default=[]),
            state=dict(
                default='present',
                choices=['present', 'absent', 'fetch']
            ),
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
