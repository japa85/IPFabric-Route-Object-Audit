from IPFabric_Connector import get_configs
from pprint import pprint
import re
from datetime import datetime
from ipfabric import IPFClient

ipf_servername = "https://ipfabric"
token  = "ipfApiToken"

Deivce_Limit = 5000

# create regex matches for route-maps, when a route-map is defined,
# 'route-map' appears at the start of line, whereas  when a route-map is referenced,
# it always has 1+ space infront of the 'route-map' command
reg_route_map_defined    = re.compile(r'^route-map (\S+)\s')
reg_route_map_referenced = re.compile(r'.* route-map (\S+)')

reg_preifx_list_defined    = re.compile(r'ip(?:v6)* prefix-list (\S+)')
reg_preifx_list_referenced = re.compile(r'.*match ip(?:v6)* address prefix-list (\S+)')

# Use IPFabric to get the device configs
# note, this function has a defined filter for NX-OS, IOS and IOS-XE devices hardcoded
def get_device_configs():
    ipf = IPFClient(ipf_servername, token)
    config_dict = get_configs(ipf, limit=Deivce_Limit)
    return config_dict


# function to look at the config and extract route-map information
def extract_info(config_dict):
    for device in config_dict:

        # load config into temp list (one line per list element)
        tmp_config = config_dict[device]['config'].split('\n')

        # define route_map lists for use later
        route_maps_defined    = list()
        route_maps_referenced = list()

        prefix_lists_defined    = list()
        prefix_lists_referenced = list()
        
        # iterate through each line of the config
        for line in tmp_config:
            # Get defined route-maps
            if re.match(reg_route_map_defined, line):
                route_maps_defined.append (re.findall(reg_route_map_defined, line)[0])
            # Get referenced route-maps
            if re.match(reg_route_map_referenced, line):
                route_maps_referenced.append (re.findall(reg_route_map_referenced, line)[0])

        for line in tmp_config:
            if re.match(reg_preifx_list_defined, line):
                prefix_lists_defined.append (re.findall(reg_preifx_list_defined, line)[0])
            if re.match(reg_preifx_list_referenced, line):
                prefix_lists_referenced.append (re.findall(reg_preifx_list_referenced, line)[0])

        # dedup lists
        route_maps_defined    = list(dict.fromkeys(route_maps_defined))
        route_maps_referenced = list(dict.fromkeys(route_maps_referenced))

        prefix_lists_defined    = list(dict.fromkeys(prefix_lists_defined))
        prefix_lists_referenced = list(dict.fromkeys(prefix_lists_referenced))

        # add info to config_dict
        config_dict[device]['Route_Maps_Defined']    = route_maps_defined
        config_dict[device]['Route_Maps_Referenced'] = route_maps_referenced

        config_dict[device]['Prefix_Lists_Defined']    = prefix_lists_defined
        config_dict[device]['Prefix_Lists_Referenced'] = prefix_lists_referenced

    return config_dict

def audit_config(config_dict):
    print ('\n\nRoute-Maps defined but not referenced:')

    sortednames=sorted(config_dict.keys(), key=lambda x:x.lower())
    
    for device in sortednames:
        # extract route-map info to make it easier to read
        route_maps_defined    = config_dict[device]['Route_Maps_Defined']
        route_maps_referenced = config_dict[device]['Route_Maps_Referenced']
       

        for rm in route_maps_defined:
            if rm not in route_maps_referenced:
                print (' > {} - {}'.format(device, rm))

    print ('\n\nRoute-Maps referenced but not defined:')
    for device in sortednames:
        # extract route-map info to make it easier to read
        route_maps_defined    = config_dict[device]['Route_Maps_Defined']
        route_maps_referenced = config_dict[device]['Route_Maps_Referenced']
        
        for rm in route_maps_referenced:
            if rm not in route_maps_defined:
                print (' > {} - {}'.format(device, rm))


    print ('\n\nPrefix-Lists defined but not referenced:')
    
    for device in sortednames:
        # extract route-map info to make it easier to read
        prefix_lists_defined    = config_dict[device]['Prefix_Lists_Defined']
        prefix_lists_referenced = config_dict[device]['Prefix_Lists_Referenced']
       

        for rm in prefix_lists_defined:
            if rm not in prefix_lists_referenced:
                print (' > {} - {}'.format(device, rm))

    print ('\n\nPrefix-Lists referenced but not defined:')
    for device in sortednames:
        # extract route-map info to make it easier to read
        prefix_lists_defined    = config_dict[device]['Prefix_Lists_Defined']
        prefix_lists_referenced = config_dict[device]['Prefix_Lists_Referenced']
        
        for rm in prefix_lists_referenced:
            if rm not in prefix_lists_defined:
                print (' > {} - {}'.format(device, rm))


      
if __name__ == "__main__":
    config_dict = get_device_configs()
    config_dict = extract_info(config_dict)
    audit_config(config_dict)
