# pip install google-api-python-client google-auth-httplib2 google-auth

import subprocess
import sys, os, json
import argparse
from flask import Flask, request, jsonify, render_template
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
#from gcp_helpers import list_zones, get_compute_engine_status, get_cloud_sql_status, get_gke_cluster_status, get_compute_summary
from gcp_helpers import GCP_Helpers

app = Flask(__name__)

# global_config = None
# global_zones = None
# global_config = {'region_prefixes':['us-'], 'projects': ['surfn-peru']}
# global_zones = []

@app.route('/report')
def report():
    data = h.get_compute_summary()
    # data['compute_keys'] = data['compute'][0].keys()
    # data['sql_keys'] = data['sql'][0].keys()
    # data['gke_keys'] = data['gke'][0].keys()
    data['compute_keys'] = ['name', 'project', 'status', 'zone', 'private_ip', 'public_ip', 'license', 'disk_size']
    data['sql_keys'] = ['name', 'project', 'state', 'zone', 'private_ip', 'public_ip', 'db_version', 'disk_size']
    data['gke_keys'] = ['name', 'project', 'status', 'location', 'ipCidr', 'public_ip', 'node_pools']
    return render_template('combined_report.html', data=data)  # Pass the data to the template

@app.route('/summary', methods=['GET'])  # Use POST for sending data
def get_compute_summary_ws():
    data = h.get_compute_summary()
    return jsonify(data), 200

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Get GCP resource status.")
    # parser.add_argument(
    #     "--project_id",
    #     required=True,  # Make project_id a required argument
    #     help="Your GCP project ID",
    # )
    # project_id = 'surfn-peru'
    # args = parser.parse_args()

    # project_id = args.project_id  # Get the project ID from command line
    # i = list_compute_images(project_id)
    # global global_config
    # global global_zones
    # global_config = dict()
    # global_zones = []

    # if os.path.exists('config.json'):
    #     with open('config.json', 'r') as f:
    #         data = f.read()
    #         global_config = json.loads(data)

    # region_prefixes = global_config.get('region_prefixes', [])

    # for project in global_config['projects']:
    #     z = list_zones(project)
    #     global_zones.extend(z)
    
    # if len(region_prefixes) > 0:
    #     global_zones = list({zone for zone in global_zones
    #             if any(zone.startswith(prefix) for prefix in region_prefixes)})
    # else:
    #     global_zones = list(set(global_zones))
    h = GCP_Helpers()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

    # x = get_compute_summary(config)
    # print(x)
    # get_cloud_sql_status(project_id)
    # get_gke_cluster_status(project_id)
