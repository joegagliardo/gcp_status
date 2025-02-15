import subprocess
import sys, os, json
import argparse
from flask import Flask, request, jsonify, render_template
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
class GCP_Helpers():
    def __init__(self, config = None, zones = None):
        if config is None:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    data = f.read()
                    self.config = json.loads(data)
            else:
                self.config = config

        if zones is None:
            self.zones = self.list_zones()
        else:
            self.zones = zones

    def list_zones(self, project_id = None):
        """Lists all GCP regions and zones."""

        credentials = GoogleCredentials.get_application_default()
        compute = discovery.build('compute', 'v1', credentials=credentials)
        projects = [project_id] if project_id is not None else self.config['projects']
        ret = []
        try:
            for project_id in projects:
                zones1 = compute.zones().list(project=project_id).execute() # List all zones for the project
    
                if 'items' in zones1:
                    for zone in zones1['items']:
                        zone_name = zone['name']
                        ret.append(zone_name)
                else:
                    print(f"    No zones found in this region.")
        except Exception as e:
            print(f"Error listing regions and zones: {e}")

        region_prefixes = self.config.get('region_prefixes', [])
        if len(region_prefixes) > 0:
            ret = list({zone for zone in ret
                    if any(zone.startswith(prefix) for prefix in region_prefixes)})
        else:
            ret = list(set(ret))
        return ret

    def get_compute_engine_status(self): 
        #project_id = None, zones = None):  # Add project_id as an argument
        """Retrieves and prints the status of Compute Engine instances."""
        credentials = GoogleCredentials.get_application_default()
        compute = discovery.build('compute', 'v1', credentials=credentials)
        ret = []
        projects = self.config['projects'] #if project_id is None else [project_id]
        zones = self.zones #if zones is None else zones
        try:
            for project_id in projects:
                for zone in zones:
                    instances = compute.instances().list(project=project_id, zone=zone).execute() # - gets all zones

                    if 'items' in instances:
                        for instance in instances['items']:
                            name = instance['name']
                            status = instance['status']
                            zone = instance['zone'].split('/')[-1]
                            private_ip = instance['networkInterfaces'][0]['networkIP']
                            public_ip = instance.get('networkInterfaces',[None])[0].get('accessConfigs', [None])[0].get('natIP', "") 

                            license = instance['disks'][0]['licenses'][0]
                            license = 'Windows' if 'windows' in license.lower() else 'Linux'                
                            disk_size = instance['disks'][0]['diskSizeGb']
                            
                            data = dict(project = project_id, name = name, status = status, zone = zone, private_ip = private_ip, public_ip = public_ip, license = license, disk_size = disk_size)
                            ret.append(data)
                    else:
                        print(f"No Compute Engine instances found in {zone}.")
        except Exception as e:
            print(f"Error retrieving Compute Engine instances: {e}")
        return ret

    def get_cloud_sql_status(self):  # Add project_id as an argument
        """Retrieves and prints the status of Cloud SQL instances."""
        credentials = GoogleCredentials.get_application_default()
        sqladmin = discovery.build('sqladmin', 'v1beta4', credentials=credentials)
        ret = []
        try:
            for project_id in self.config['projects']:
                instances = sqladmin.instances().list(project=project_id).execute()
                if 'items' in instances:
                    #print("\nCloud SQL Instances:")
                    for instance in instances['items']:
                        name = instance['name']
                        state = instance['state']
                        db_version = instance['databaseVersion']
                        disk_size = instance['settings']['dataDiskSizeGb']
                        zone = instance['gceZone']
                        ips = {x['type']: x['ipAddress'] for x in instance['ipAddresses']}
                        private_ip = ips.get('PRIVATE', "")
                        public_ip = ips.get('PRIMARY', "")
                        ret.append(dict(project = project_id, name = name, state = state, db_version = db_version, disk_size = disk_size, zone = zone, private_ip = private_ip, public_ip = public_ip))
                else:
                    print(f"No Cloud SQL instances found in project {project_id}.")

        except Exception as e:
            print(f"Error retrieving Cloud SQL instances: {e}")
        return ret

    def get_gke_cluster_status(self):
        """Retrieves and prints the status of GKE clusters."""
        credentials = GoogleCredentials.get_application_default()
        container = discovery.build('container', 'v1beta1', credentials=credentials)

        ret = []
        # we need to search both zone and region, so I will loop through twice, first on zone, and then on region
        zones1 = self.zones.copy()
        for cnt in range(1, 3):
            if cnt == 2:
                zones1 = {zone[:-2] for zone in self.zones}
            for project_id in self.config['projects']:
                for zone in zones1:
                    try:
                        clusters = container.projects().locations().clusters().list(parent=f"projects/{project_id}/locations/{zone}").execute()
                        if 'clusters' in clusters:
                            #print("\nGKE Clusters:")
                            for cluster in clusters['clusters']:
                                name = cluster['name'].split('/')[-1]
                                status = cluster['status']
                                location = cluster['location']
                                ipCidr = cluster['clusterIpv4Cidr']
                                node_pools = len(cluster['nodePools'])
                                public_ip = cluster['endpoint']
                                ret.append(dict(project = project_id, name = name, status = status, location = location, ipCidr = ipCidr, node_pools = node_pools, public_ip = public_ip))
                                # private_ip
                                # 'publicEndpoint': '35.239.194.41', 'privateEndpoint': '10.128.0.81'}}, 
                                # print(cluster)
                                # print(f"  - {name} (Location: {location}): {status}")
                        else:
                            print("No GKE clusters found.")

                    except Exception as e:
                        print(f"Error retrieving GKE clusters: {e}")
        return ret

    def get_compute_summary(self):
        # global global_config
        # config = global_config if config is None else config
        results = {'compute': [], 'sql': [], 'gke': [], 'load_balancer': [], 'backend_service': []}
        c = self.get_compute_engine_status()
        results['compute'].extend(c)
        s = self.get_cloud_sql_status()
        results['sql'].extend(s)
        k = self.get_gke_cluster_status()
        results['gke'].extend(k)
        # for project_id in config['projects']:
        #     # zones = [zone for zone in list_zones(project_id) 
        #     #          if any(continent + '-' in zone for continent in config['continents'])]
        #     #print(zones)
        #     c = get_compute_engine_status(project_id, zones = zones1)
        #     results['compute'].extend(c)
        #     s = get_cloud_sql_status(project_id)
        #     results['sql'].extend(s)
        #     g = get_gke_cluster_status(project_id, zones = zones1)
        #     results['gke'].extend(g)
        return results



# from googleapiclient import discovery
# from oauth2client.client import GoogleCredentials

# def list_compute_images(project_id="your-project-id"):  # Replace with your project ID or make it a parameter
#     """Lists Compute Engine images."""

#     credentials = GoogleCredentials.get_application_default()
#     compute = discovery.build('compute', 'v1', credentials=credentials)

#     try:
#         images = compute.images().list(project=project_id).execute()

#         if 'items' in images:
#             print("Compute Engine Images:")
#             for image in images['items']:
#                 name = image['name']
#                 # Add other properties you want to display, e.g.,
#                 # creationTimestamp, description, diskSizeGb, etc.
#                 creation_timestamp = image.get('creationTimestamp', 'N/A')  # Handle potential missing keys
#                 disk_size_gb = image.get('diskSizeGb', 'N/A')
#                 source_image = image.get('sourceImage', 'N/A') # The source image used to create the image
#                 print(f"  - {name} (Created: {creation_timestamp}, Size: {disk_size_gb} GB, Source Image: {source_image})")
#         else:
#             print("No Compute Engine images found.")

#     except Exception as e:
#         print(f"Error listing images: {e}")


# def install_packages():
#     """Installs required packages if they are not already installed."""
#     try:
#         # Check if the required packages are already installed.  If not, an ImportError will be raised.
#         from googleapiclient import discovery
#         from oauth2client.client import GoogleCredentials
#         return 0

#     except ImportError:
#         print("Installing required packages...")
#         try:
#             # Construct the pip install command.  Use sys.executable to ensure the correct pip is used.
#             packages = ["google-api-python-client", "google-auth", "google-auth-httplib2"]
#             subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)  # Check for errors
#             print("Packages installed successfully.")
#             return 1

#         except subprocess.CalledProcessError as e:
#             print(f"Error installing packages: {e}")
#             sys.exit(1) # Exit the script if package installation fails


# install_packages()  # Call the install function *before* using the libraries
