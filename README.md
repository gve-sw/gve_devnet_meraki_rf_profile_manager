# GVE DevNet Meraki RF Profile Manager
This repository contains code for a Flask app that displays basic information about Meraki access points (model, serial, network, etc.) as well as the associated RF Profile. The access points can be filtered by model and RF profile.

The RF Profile can be updated through the app as well with any available RF Profiles present on the AP's network.

![/IMAGES/rf_profile_manager_workflow.png](/IMAGES/rf_profile_manager_workflow.png)

## Contacts
* Danielle Stacy
* Trevor Maco

## Solution Components
* Meraki
* Flask
* SQLite
* Flask SQLAlchemy

## Prerequisites
#### Meraki API Keys
In order to use the Meraki API, you need to enable the API for your organization first. After enabling API access, you can generate an API key. Follow these instructions to enable API access and generate an API key:
1. Login to the Meraki dashboard
2. In the left-hand menu, navigate to `Organization > Settings > Dashboard API access`
3. Click on `Enable access to the Cisco Meraki Dashboard API`
4. Go to `My Profile > API access`
5. Under API access, click on `Generate API key`
6. Save the API key in a safe place. The API key will only be shown once for security purposes, so it is very important to take note of the key then. In case you lose the key, then you have to revoke the key and a generate a new key. Moreover, there is a limit of only two API keys per profile.

> For more information on how to generate an API key, please click [here](https://developer.cisco.com/meraki/api-v1/#!authorization/authorization). 

> Note: You can add your account as Full Organization Admin to your organizations by following the instructions [here](https://documentation.meraki.com/General_Administration/Managing_Dashboard_Access/Managing_Dashboard_Administrators_and_Permissions).

## Installation/Configuration
1. Clone this repository with `git clone [repository name]`
2. Add the Meraki API key and organization name to environment variables
```python
API_KEY = "API key goes here"
ORG_NAME = "organization name goes here"
```
> For more information about environmental variables, read [this article](https://dev.to/jakewitcher/using-env-files-for-environment-variables-in-python-applications-55a1)
3. Set up a Python virtual environment. Make sure Python 3 is installed in your environment, and if not, you may download Python [here](https://www.python.org/downloads/). Once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](https://docs.python.org/3/tutorial/venv.html).
4. Install the requirements with `pip3 install -r requirements.txt`

## Usage
This web app was written to call the information about the access points from a database. The file `db.py` contains a script to create and then populate this database with the access points in the Meraki organization specified in the `.env` file. This is strictly necessary only once for initial setup, but it can be run periodically to ensure the DB is consistent with the Meraki organization's APs.
To run this script, use the command:
```
$ python3 db.py
```

* Optional: A cronjob can be created to periodically run `db.py` to ensure the database remains consistent with the Meraki Org. Please consult `crontab.txt` for more information.

To start the web app that is written in the file `app.py`, use the command:
```
$ flask run
```

Then navigate to the flask URL.

There are 2 main workflows (and pages): AP Display, and AP RF Profile Updating.

* AP Display - View organization-wide AP information, with filtering options by model and RF Profile.

![/IMAGES/rf_profile_display.png](/IMAGES/rf_profile_display.png)

* AP RF Profile Update - Update 1 or more AP's RF Profile.

![/IMAGES/rf_profile_update.png](/IMAGES/rf_profile_update.png)
  

# Screenshots
![/IMAGES/0image.png](/IMAGES/0image.png)


## LICENSE
Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

## CODE_OF_CONDUCT
Our code of conduct is available [here](CODE_OF_CONDUCT.md)

## CONTRIBUTING
See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without       any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools       is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not          responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
