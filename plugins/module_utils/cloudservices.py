#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
---
author: Alex Shemyakin
short_description: HttpApi Plugin for F5 Cloud Services
description:
  - This HttpApi plugin provides methods to connect to F5 Cloud Services over a HTTP(S)-based api.
version_added: "1.0"
"""

import re
from ansible.errors import AnsibleConnectionFailure

f5_cs_eap_default_policy = {
    "compliance_enforcement": {
      "data_guard": {
        "cc": True,
        "enabled": True,
        "ssn": True
      },
      "enabled": True,
      "sensitive_parameters": {
        "enabled": True,
        "parameters": [
          "cc_id",
          "creditcard",
          "passwd",
          "password"
        ]
      }
    },
    "encoding": "utf-8",
    "high_risk_attack_mitigation": {
      "allowed_methods": {
        "enabled": True,
        "methods": [
          {
            "name": "GET"
          },
          {
            "name": "POST"
          },
          {
            "name": "HEAD"
          }
        ]
      },
      "api_compliance_enforcement": {
        "enabled": True
      },
      "disallowed_file_types": {
        "enabled": True,
        "file_types": [
          "back",
          "bat",
          "bck",
          "bin",
          "cfg",
          "cmd",
          "com",
          "config",
          "dat",
          "dll",
          "eml",
          "exe",
          "exe1",
          "exe_renamed",
          "hta",
          "htr",
          "htw",
          "ida",
          "idc",
          "idq",
          "ini",
          "old",
          "sav",
          "save"
        ]
      },
      "enabled": True,
      "enforcement_mode": "monitoring",
      "geolocation_enforcement": {
        "disallowed_country_codes": [
          "CU",
          "IR",
          "KP",
          "LY",
          "SD",
          "SY"
        ],
        "enabled": True
      },
      "http_compliance_enforcement": {
        "enabled": True
      },
      "ip_enforcement": {
        "enabled": True,
        "ips": [

        ]
      },
      "signature_enforcement": {
        "enabled": True
      }
    },
    "malicious_ip_enforcement": {
      "enabled": True,
      "enforcement_mode": "monitoring",
      "ip_categories": [
        {
          "block": True,
          "log": True,
          "name": "mobile_threats"
        },
        {
          "block": True,
          "log": True,
          "name": "cloud_services"
        },
        {
          "block": True,
          "log": True,
          "name": "anonymous_proxies"
        },
        {
          "block": True,
          "log": True,
          "name": "phishing_proxies"
        },
        {
          "block": True,
          "log": True,
          "name": "infected_sources"
        },
        {
          "block": True,
          "log": True,
          "name": "denial_of_service"
        },
        {
          "block": True,
          "log": True,
          "name": "scanners"
        },
        {
          "block": True,
          "log": True,
          "name": "bot_nets"
        },
        {
          "block": True,
          "log": True,
          "name": "web_attacks"
        },
        {
          "block": True,
          "log": True,
          "name": "windows_exploits"
        },
        {
          "block": True,
          "log": True,
          "name": "spam_sources"
        }
      ]
    },
    "threat_campaigns": {
      "campaigns": [

      ],
      "enabled": True,
      "enforcement_mode": "monitoring"
    }
}

BASE_HEADERS = {'Content-Type': 'application/json'}
LOGIN_URL = "/v1/svc-auth/login"
LOGOUT_URL = "/v1/svc-auth/logout"
RELOG_URL = "/v1/svc-auth/relogin"
SUBSCRIPTION_BY_ID_URL = "/v1/svc-subscription/subscriptions/{0}"
SUBSCRIPTIONS_BY_TYPE = "/v1/svc-subscription/subscriptions?service_type={0}&account_id={1}"
SUBSCRIPTION_URL = "/v1/svc-subscription/subscriptions"
SUBSCRIPTION_STATUS_URL = "/v1/svc-subscription/subscriptions/{0}/status"
ACTIVATE_SUBSCRIPTION_URL = "/v1/svc-subscription/subscriptions/{0}/activate"
SUSPEND_SUBSCRIPTION_URL = "/v1/svc-subscription/subscriptions/{0}/suspend"
RETIRE_SUBSCRIPTION_URL = "/v1/svc-subscription/subscriptions/{0}/retire"
GET_CURRENT_USER = "/v1/svc-account/user"
GET_CATALOGS = "/v1/svc-catalog/catalogs"
GET_ACCOUNT_CATALOGS = "/v1/svc-account/accounts/{0}/catalogs"
POST_CATALOGS = "/v1/svc-account/accounts/{0}/catalogs"
DELETE_CATALOGS = "/v1/svc-account/accounts/{0}/catalogs/{1}"
CERTIFICATES_URL = "/v1/svc-certificates/certificates"
GET_CERTIFICATES_URL = "/v1/svc-certificates/certificates/{0}"
DELETE_CERTIFICATES_URL = "/v1/svc-certificates/{0}"
BATCH_GET_ACCOUNTS = "/v1/svc-account/accounts/batch-get"
CREATE_ACCOUNT = "/v1/svc-account/accounts"
UPDATE_ACCOUNT = "/v1/svc-account/accounts/{0}"
DELETE_ACCOUNT = "/v1/svc-account/accounts/{0}?cascade={1}"
DELETE_ACCOUNT_MEMBER = "/v1/svc-account/accounts/{0}/members/{1}"
DELETE_INVITE = "/v1/svc-account/invites/{0}"
GET_ACCOUNT = "/v1/svc-account/accounts/{0}"
GET_MEMBERSHIPS = "/v1/svc-account/users/{0}/memberships"
GET_ACCOUNT_MEMBERS = "/v1/svc-account/accounts/{0}/members"
GET_INVITES = "/v1/svc-account/invites"
UPDATE_ACCOUNT_MEMBER = "/v1/svc-account/accounts/{0}/members/{1}"
CREATE_INVITE_INTO_ACCOUNT = "/v1/svc-account/invites"


class CloudservicesApi():
    def __init__(self, connection, account_id=None):
        self.connection = connection
        self.account_id = account_id

    def handle_httperror(self, response):
        err_4xx = r'^4\d{2}$'
        handled_error = re.search(err_4xx, str(response['code']))
        if handled_error:
            raise AnsibleConnectionFailure(response['contents'])
        return False

    def get_subscription_by_id(self, subscription_id):
        if subscription_id:
            response = self.connection.get(url=SUBSCRIPTION_BY_ID_URL.format(subscription_id), account_id=self.account_id)
            self.handle_httperror(response)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Subscription Id is required.')

    def get_subscriptions_by_type(self, subscription_type, account_id):
        if subscription_type:
            response = self.connection.get(url=SUBSCRIPTIONS_BY_TYPE.format(subscription_type, account_id), account_id=self.account_id)
            self.handle_httperror(response)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Subscription Type is required.')

    def create_subscription(self, payload):
        if payload:
            response = self.connection.post(url=SUBSCRIPTION_URL, data=payload, account_id=self.account_id)
            self.handle_httperror(response)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Payload is empty.')

    def update_subscription(self, payload, subscription_id):
        if payload:
            response = self.connection.put(url=SUBSCRIPTION_BY_ID_URL.format(subscription_id), data=payload, account_id=self.account_id)
            self.handle_httperror(response)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Payload is empty.')

    def retire_subscription(self, payload, subscription_id):
        response = self.connection.post(url=RETIRE_SUBSCRIPTION_URL.format(subscription_id), data=payload, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def activate_subscription(self, subscription_id):
        response = self.connection.post(url=ACTIVATE_SUBSCRIPTION_URL.format(subscription_id), account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def suspend_subscription(self, subscription_id):
        response = self.connection.post(url=SUSPEND_SUBSCRIPTION_URL.format(subscription_id), account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def get_subscription_status(self, subscription_id):
        response = self.connection.get(url=SUBSCRIPTION_STATUS_URL.format(subscription_id), account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def get_current_user(self):
        response = self.connection.get(url=GET_CURRENT_USER, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def get_catalogs(self):
        response = self.connection.get(url=GET_CATALOGS, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def enable_catalog_item(self, payload, account_id):
        response = self.connection.post(url=POST_CATALOGS.format(account_id), data=payload, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def disable_catalog_item(self, account_id, catalog_id):
        response = self.connection.delete(url=DELETE_CATALOGS.format(account_id, catalog_id), account_id=account_id)
        self.handle_httperror(response)
        return response['contents']

    def post_certificate(self, payload):
        response = self.connection.post(url=CERTIFICATES_URL, data=payload, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def get_certificates(self, account_id):
        response = self.connection.get(url=GET_CERTIFICATES_URL.format(account_id), account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def retire_certificate(self, certificate_id):
        response = self.connection.delete(url=DELETE_CERTIFICATES_URL.format(certificate_id), account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def batch_get_accounts(self, payload):
        response = self.connection.post(url=BATCH_GET_ACCOUNTS, data=payload, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def update_account(self, payload, account_id):
        if payload:
            response = self.connection.put(url=UPDATE_ACCOUNT.format(account_id), data=payload, account_id=self.account_id)
            self.handle_httperror(response)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Payload is empty.')

    def get_memberships(self, user_id):
        response = self.connection.get(url=GET_MEMBERSHIPS.format(user_id), account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def get_account(self, account_id):
        response = self.connection.get(url=GET_ACCOUNT.format(account_id), account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def create_account(self, payload):
        response = self.connection.post(url=CREATE_ACCOUNT, data=payload, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def delete_account(self, payload, account_id, cascade):
        response = self.connection.delete(url=DELETE_ACCOUNT.format(account_id, str(cascade).lower()), data=payload, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def delete_account_member(self, account_id, user_id):
        response = self.connection.delete(url=DELETE_ACCOUNT_MEMBER.format(account_id, user_id), account_id=account_id)
        self.handle_httperror(response)
        return response['contents']

    def delete_invite(self, invite_id):
        response = self.connection.delete(url=DELETE_INVITE.format(invite_id), account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def list_account_members(self, account_id):
        response = self.connection.get(url=GET_ACCOUNT_MEMBERS.format(account_id), account_id=account_id)
        self.handle_httperror(response)
        return response['contents']

    def list_invites(self):
        response = self.connection.get(url=GET_INVITES, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']

    def update_account_member(self, payload, account_id, user_id):
        response = self.connection.put(url=UPDATE_ACCOUNT_MEMBER.format(account_id, user_id), data=payload, account_id=account_id)
        self.handle_httperror(response)
        return response['contents']

    def create_invite_into_account(self, payload):
        response = self.connection.post(url=CREATE_INVITE_INTO_ACCOUNT, data=payload, account_id=self.account_id)
        self.handle_httperror(response)
        return response['contents']