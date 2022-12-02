# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2022 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Trevor Maco <tmaco@cisco.com>, Danielle Stacy <dastacy@cisco.com>"
__copyright__ = "Copyright (c) 2022 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

# Imports
import requests
import sys
import json


def get_org_id(org_name, api_essentials):
    """Get Org Id"""

    # api essentials
    base_url = api_essentials['base_url']
    headers = api_essentials['headers']

    org_endpoint = 'organizations'

    response = requests.get(url=f'{base_url}{org_endpoint}', headers=headers)

    if response.status_code == 200:
        orgs = response.json()

        for org in orgs:
            if org['name'] == org_name:
                return org['id']

        return None
    else:
        print(f'GET orgs message failed: {response.text}')
        sys.exit(1)


def get_access_points(api_essentials, org_id):
    """Get Org AP Inventory"""

    # api essentials
    base_url = api_essentials['base_url']
    headers = api_essentials['headers']

    inventory_endpoint = f'organizations/{org_id}/devices'

    params = {
        'productTypes[]': ['wireless']
    }

    response = requests.get(url=f'{base_url}{inventory_endpoint}', headers=headers, params=params)

    if response.status_code == 200:
        devices = response.json()
        access_points = []

        # Grab all the aps
        for device in devices:
            access_points.append(device)

        # sort ap's by model number
        access_points_sorted = sorted(access_points, key=lambda d: d['model'])

        return access_points_sorted
    else:
        print(f'GET org ap\'s failed: {response.text}')
        sys.exit(1)


def get_network_name(api_essentials, networkId, session):
    """Get network name from network id"""

    # api essentials
    base_url = api_essentials['base_url']
    headers = api_essentials['headers']

    net_endpoint = f'/networks/{networkId}'

    print(f'Getting network name for network id: {networkId}')

    response = session.get(url=f'{base_url}{net_endpoint}', headers=headers)

    if response.status_code == 200:
        return response.json()['name']
    else:
        print(f'GET rf profile id failed: {response.text}')
        sys.exit(1)


def get_rf_profile_id(api_essentials, device_serial, session):
    """Get the RF profile id of an AP"""

    # api essentials
    base_url = api_essentials['base_url']
    headers = api_essentials['headers']

    rf_endpoint = f'devices/{device_serial}/wireless/radio/settings'

    print(f'Getting rf profile for {device_serial}')

    response = session.get(url=f'{base_url}{rf_endpoint}', headers=headers)

    if response.status_code == 200:
        return response.json()['rfProfileId']
    else:
        print(f'GET rf profile id failed: {response.text}')
        sys.exit(1)


def get_rf_profile_name(api_essentials, networkId, rfProfileId, session):
    """Translate rf id into a rf name"""

    # api essentials
    base_url = api_essentials['base_url']
    headers = api_essentials['headers']

    rf_endpoint = f'networks/{networkId}/wireless/rfProfiles/{rfProfileId}'

    print(f'Getting rf profile name for id {rfProfileId}')

    response = session.get(url=f'{base_url}{rf_endpoint}', headers=headers)

    if response.status_code == 200:
        return response.json()['name']
    else:
        print(f'GET rf profile name failed: {response.text}')
        sys.exit(1)


def get_rf_profiles(api_essentials, networkId, session):
    """Retrieve all RF profiles in a network"""
    
    base_url = api_essentials['base_url']
    headers = api_essentials['headers']

    rf_endpoint = f'networks/{networkId}/wireless/rfProfiles'

    print(f'Getting rf profiles for network {networkId}')

    response = session.get(url=f'{base_url}{rf_endpoint}', headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f'GET rf profiles for network {networkId} failed: {response.text}')
        sys.exit(1)


def update_ap_rf_profile(api_essentials, serial, rfProfileId, session):
    """Update the RF profile of the AP"""

    base_url = api_essentials['base_url']
    headers = api_essentials['headers']

    ap_endpoint = f'devices/{serial}/wireless/radio/settings'

    if rfProfileId == "Indoor" or rfProfileId == "Outdoor" or rfProfileId == "Unknown" or rfProfileId == "None":
        rfProfileId = None

    body = {"rfProfileId": rfProfileId}

    response = session.put(url=f'{base_url}{ap_endpoint}', headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        return response.json()
    else:
        print(f'Update ap rf profile failed: {response.text}')

        return None
