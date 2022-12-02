""" Copyright (c) 2020 Cisco and/or its affiliates.
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

import sqlite3
from sqlite3 import Error
from dotenv import load_dotenv
import os
from pprint import pprint

from requests.adapters import HTTPAdapter, Retry

from meraki_functions import *

# Note: these are lists of indoor and outdoor ap's at the time of writing, please update if a newer/older model is
# not present in the appropriate list
indoor_aps = ['MR16', 'MR18', 'MR20', 'MR28', 'CW9162', 'CW9164', 'CW9166', 'MR36H', 'MR20', 'MR44', 'MR46', 'MR30H', 'MR36', 'MR46E', 'MR52', 'MR56', 'MR57']
outdoor_aps = ['MR78', 'MR70', 'MR76', 'MR86']

def create_connection(db_file):
    """ Create DB Connection object """

    conn = None
    try:
        conn = sqlite3.connect(db_file)

        return conn
    except Error as e:
        print(e)
        return None

def create_tables(conn):
    """ Create Tables: networks, profiles, aps. Networks hold network ID and name. Profiles hold rf profile id and
    name. APs hold serial, model, IP, address, and relations to network ID and rf profile ID. """

    c = conn.cursor()

    # Network table
    c.execute("""
        CREATE TABLE IF NOT EXISTS networks
        ([networkId] TEXT PRIMARY KEY,
        [networkName] TEXT)
    """)

    # Profile Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS profiles
        ([rfProfileId] TEXT PRIMARY KEY,
        [rfProfileName] TEXT,
        [networkId] TEXT,
        FOREIGN KEY (networkId) REFERENCES networks (networkId))
    """)

    # APs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS aps
        ([serial] TEXT PRIMARY KEY, 
        [model] TEXT, 
        [networkId] TEXT,
        [rfProfileId] TEXT,
        [lanIp] TEXT,
        [address] TEXT,
        FOREIGN KEY (networkId) REFERENCES networks (networkId),
        FOREIGN KEY (rfProfileId) REFERENCES profiles (rfProfileId))
    """)

    conn.commit()

def populate_db(conn):
    """ Query org and populate tables with AP information, their corresponding networks, and their corresponding
    rfPRofile in each respective table """

    c = conn.cursor()

    api_essentials = {
        'base_url': 'https://api.meraki.com/api/v1/',
        'headers': {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Cisco-Meraki-API-Key": os.getenv("MERAKI_API_KEY")
        }
    }
    org_name = os.getenv("ORG_NAME")

    # Get org ID
    org_id = get_org_id(org_name, api_essentials)
    if org_id is None:
        print("Could not populate database: There was an issue retrieving the Meraki organization id")

        return

    # Get AP's org wide
    aps = get_access_points(api_essentials, org_id)

    # For rate limiting, use backoff strategy
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    nets = []
    seen_profiles = []

    # Build out each DB entry
    for ap in aps:
        if ap["address"] == "":
            ap["address"] = "None"

        if ap["lanIp"] is None:
            ap["lanIp"] = "None"

        # Get rf profile id
        rf_id = get_rf_profile_id(api_essentials, ap["serial"], session)
        seen_profiles.append(rf_id)

        # Get network name
        net_name = get_network_name(api_essentials, ap["networkId"], session)
        nets.append(ap["networkId"])

        # Get rf profile name (or default name if using default rf profile)
        if rf_id is None:
            rf_id = "None"
            if ap["model"] in indoor_aps:
                rf_name = "Default Indoor Profile"
            elif ap["model"] in outdoor_aps:
                rf_name = "Default Outdoor Profile"
            else:
                rf_name = "UNKNOWN"
        else:
            # Add new rf profile name field
            rf_name = get_rf_profile_name(api_essentials, ap["networkId"], rf_id, session)

        # Insert values into DB tables
        c.execute("""INSERT OR REPLACE INTO networks (networkId, networkName)
            VALUES (?, ?)""",
            (ap["networkId"], net_name)
        )

        if rf_id != "None":
            c.execute("""INSERT OR REPLACE INTO profiles (rfProfileId, rfProfileName, networkId)
                VALUES (?, ?, ?)""",
                (rf_id, rf_name, ap["networkId"])
            )
        else:
            c.execute("""INSERT OR REPLACE INTO profiles (rfProfileId, rfProfileName)
                VALUES (?, ?)""",
                (rf_id, rf_name))

        c.execute("""INSERT OR REPLACE INTO aps (serial, model, networkId, rfProfileId, lanIp, address) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (ap["serial"], ap["model"], ap["networkId"], rf_id, ap["lanIp"], ap["address"])
        )

        conn.commit()

    # Collect all rf profiles for every network, look for rf profiles which haven't been assigned to an AP,
    # add them to the profiles DB
    profiles = []

    for net in nets:
        profiles.extend(get_rf_profiles(api_essentials, net, session))

    for profile in profiles:
        pprint(profile)
        if profile['id'] not in seen_profiles:
            c.execute("""INSERT OR REPLACE INTO profiles (rfProfileId, rfProfileName, networkId)
                VALUES (?, ?, ?)""",
                (profile["id"], profile["name"], profile["networkId"])
            )
            conn.commit()


def queryAllAPs(conn):
    c = conn.cursor()
    print(c.execute("SELECT * FROM aps").fetchall())

def queryAllProfiles(conn):
    c = conn.cursor()
    print(c.execute("SELECT * FROM profiles").fetchall())

def queryAllNetworks(conn):
    c = conn.cursor()
    print(c.execute("SELECT * FROM networks").fetchall())

def querySpecificAP(conn, col, serial):
    c = conn.cursor()
    query_result = c.execute(f"SELECT {col} FROM aps WHERE serial=?", (serial,)).fetchall()

    return query_result

def queryAll(conn):
    c = conn.cursor()
    print(c.execute("""SELECT * 
                    FROM aps 
                    JOIN profiles 
                    ON aps.rfProfileId = profiles.rfProfileId
                    JOIN networks
                    ON aps.networkId = networks.networkId""").fetchall())

def close_connection(conn):
    conn.close()

if __name__ == "__main__":
    load_dotenv()

    conn = create_connection("sqlite.db")
    if conn is not None:
        create_tables(conn)
        populate_db(conn)
        queryAllAPs(conn)
        queryAllProfiles(conn)
        queryAllNetworks(conn)
        queryAll(conn)

        close_connection(conn)