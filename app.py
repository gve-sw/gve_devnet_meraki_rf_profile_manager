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

# Import Section
from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import datetime
import paginate_sqlalchemy
import os
from dotenv import load_dotenv
from collections import defaultdict

from requests.adapters import HTTPAdapter, Retry

from meraki_functions import *

# Global variables
load_dotenv()

app = Flask(__name__)

# specify name of database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"

# connect existing SQLite db to FlaskSQLAlchemy
Base = automap_base()

engine = create_engine("sqlite:///sqlite.db", connect_args={'check_same_thread': False})

Base.prepare(engine, reflect=True)

# DB Tables
AP = Base.classes.aps
Network = Base.classes.networks
Profile = Base.classes.profiles

db_session = Session(engine)


# Methods
def getSystemTimeAndLocation():
    """Returns location and time of accessing device"""
    # request user ip
    userIPRequest = requests.get('https://get.geojs.io/v1/ip.json')
    userIP = userIPRequest.json()['ip']

    # request geo information based on ip
    geoRequestURL = 'https://get.geojs.io/v1/ip/geo/' + userIP + '.json'
    geoRequest = requests.get(geoRequestURL)
    geoData = geoRequest.json()

    # create info string
    location = geoData['country']
    timezone = geoData['timezone']
    current_time = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    timeAndLocation = "System Information: {}, {} (Timezone: {})".format(location, current_time, timezone)

    return timeAndLocation


@app.route('/display/<page>')
def display(page):
    """Main display page. Displays paginated list of APs with/without filters applied. """
    try:
        # Query for unique APs models and profiles
        query = db_session.query(AP.model).distinct().all()
        models = [record[0] for record in query]

        query = db_session.query(Profile.rfProfileName).distinct().all()
        profiles = [record[0] for record in query]

        # Sort models and RF Profiles
        models.sort()
        profiles.sort()

        # url params
        model = request.args.get('model')
        rf_profile = request.args.get('rf_profile')

        # get access points in the org (join with other tables for values)
        ap_query = db_session.query(AP).join(Network, AP.networkId == Network.networkId).join(Profile, Profile.rfProfileId == AP.rfProfileId)

        # apply filter criteria to query if necessary
        if model is not None and rf_profile is not None:
            if model != "--- Select an AP model ---" and rf_profile != "--- Select an RF profile ---":
                ap_query = ap_query.filter(AP.model == model, Profile.rfProfileName == rf_profile)
            elif model != "--- Select an AP model ---":
                ap_query = ap_query.filter(AP.model == model)
            elif rf_profile != "--- Select an RF profile ---":
                ap_query = ap_query.filter(Profile.rfProfileName == rf_profile)

        # use pagination to grab subset
        curr_page = paginate_sqlalchemy.SqlalchemyOrmPage(ap_query, page=page, items_per_page=12)

        # pagination display information
        pagination = {
            'page': curr_page.page,
            'first_page': curr_page.first_page,
            'last_page': curr_page.last_page,
            'previous_page': curr_page.previous_page,
            'next_page': curr_page.next_page,
            'page_count': curr_page.page_count
        }

        # Filtering information
        filtering = {
            "models": models,
            "profiles": profiles,
            "curr_model": model,
            "curr_profile": rf_profile
        }

        # Create access points dictionary for front end
        access_points_page = []
        for ap in curr_page.items:
            access_points_page.append({
                "address": ap.address,
                "lanIp": ap.lanIp,
                "model": ap.model,
                "networkId": ap.networkId,
                'networkName': ap.networks.networkName,
                'rfProfileId': ap.rfProfileId,
                'rfProfileName': ap.profiles.rfProfileName,
                'serial': ap.serial
            })

        return render_template('tile-template.html', hiddenLinks=False, timeAndLocation=getSystemTimeAndLocation(),
                               access_points=access_points_page, filtering=filtering, pagination=pagination)

    except Exception as e:
        print(e)
        # OR the following to show error message
        return render_template('instructions.html', error=False, errormessage="CUSTOMIZE: Add custom message here.",
                               errorcode=e, timeAndLocation=getSystemTimeAndLocation())


@app.route('/')
def index():
    """Main landing page - redirect to display page, no filters applied, page 1"""
    return redirect(
        url_for('display', page=1, model="--- Select an AP model ---", rf_profile="--- Select an RF profile ---"))


@app.route('/update')
def update():
    """ Update page: display networks, APs, and rf profiles to select from. User will make appropriate selections
    and kick off update process. """

    try:
        # Get all APs
        ap_query = db_session.query(AP)
        access_points = [ap.__dict__ for ap in ap_query]

        models = []
        networks = []
        profile_networks = defaultdict(list)
        net_id_to_name = {}

        # For each ap, add the network name and rfprofile name to ap object, add unique models and networks to lists
        for ap in access_points:
            net_id = ap['networkId']
            rf_id = ap['rfProfileId']

            # Get rfprofileName
            profile_query = db_session.query(Profile).filter_by(rfProfileId=rf_id).one()
            profile = profile_query.__dict__
            rf_name = profile['rfProfileName']
            ap['rfProfileName'] = rf_name

            # Get network name
            network_query = db_session.query(Network).filter_by(networkId=net_id).one()
            network = network_query.__dict__
            net_name = network['networkName']
            ap['networkName'] = net_name
            net_id_to_name[net_id] = net_name

            if ap['model'] not in models:
                models.append(ap['model'])

            if net_name not in networks:
                networks.append(net_name)

        # Get all rfprofiles, build a list of networks and their profile names
        all_profiles_query = db_session.query(Profile)
        all_profiles = [profile.__dict__ for profile in all_profiles_query]
        print(all_profiles)

        # Add each profile to the network it's configured on
        for profile in all_profiles:
            net_id = profile["networkId"]
            if net_id is None:
                profile_networks['all'].append(profile)
            else:
                net_name = net_id_to_name[net_id]
                profile_networks[net_name].append(profile)

        return render_template('edit.html', hiddenLinks=False, timeAndLocation=getSystemTimeAndLocation(),
                               access_points=access_points, models=models, networks=networks,
                               profile_networks=profile_networks)

    except Exception as e:
        print(e)

        return render_template('tile-template.html', hiddenLinks=False, error=False,
                               errormessage="issue with displaying aps to edit",
                               errorcode=e)


@app.route('/changeprofile', methods=['POST'])
def changeProfile():
    """Update rfprofile of selected AP(s), Meraki will update AP, DB will be updated, flask app will display AP with
    new profile """
    if request.method == 'POST':

        # Parameters
        serials = request.json['serials']
        rf_profile_name = request.json['profile']

        errors = []
        success = []

        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        api_essentials = {
            'base_url': 'https://api.meraki.com/api/v1/',
            'headers': {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Cisco-Meraki-API-Key": os.getenv("MERAKI_API_KEY")
            }
        }

        for serial in serials:
            if rf_profile_name != "Default Indoor Profile" and rf_profile_name != "Default Outdoor Profile":
                ap_network_query = db_session.query(AP).filter_by(serial=serial).one()
                ap_network = ap_network_query.__dict__['networkId']
                profile_query = db_session.query(Profile).filter_by(rfProfileName=rf_profile_name,
                                                                    networkId=ap_network).one()
                profile = profile_query.__dict__
                profile_id = profile['rfProfileId']
            else:
                profile_id = None

            # Meraki API call to update rfprofile of AP
            update_response = update_ap_rf_profile(api_essentials, serial, profile_id, session)
            if update_response is None:
                print(f'There was an issue trying to update the rf profile of ap {serial} to {rf_profile_name}')
                error = {"profile": rf_profile_name, "serial": serial}
                errors.append(error)
            else:
                success.append(update_response)

                if profile_id is None:
                    profile_id = "None"

                # Update DB entry for AP
                ap_query = db_session.query(AP).filter_by(serial=serial).one()
                ap_query.rfProfileId = profile_id
                db_session.commit()

        return {"success": success, "error": errors}


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
