import json
from pprint import pprint
from ipfabric import IPFClient
#define IPFabric Objects


def get_configs(ipf: IPFClient, limit):

    # return a list of devices using pre-defined filters for nxos and ios/ios-xe devices
    snapshotId = '$last'    
    EndPoint = "tables/inventory/devices"
    Payload = { "columns":
                    ["hostname"],
                "filters": {"and": [{"vendor": ["eq","cisco"]},{"or": [{"family": ["eq","ios"]},{"family": ["eq","ios-xe"]},{"family": ["eq","nx-os"]}]}]},
                "pagination":
                    { "limit": limit,  "start": 0 },
                "snapshot": snapshotId,
                "reports": "/inventory/devices"
                }
    
    output = ipf.post(url=EndPoint, json=Payload)
    
    tmp_dict_devices = output.json()['data']

    # reformat output to make it easier to get associated hash value later
    tmp_device_hash = dict()
    for var in tmp_dict_devices:
        tmp_device_hash[var['hostname']] = str()

    # get config hashs, cant finder on anything other than hostname, so will need to collect and
    # and sort ourselves
    EndPoint = "/tables/management/configuration"
    Payload = {
        "columns":[
            "hash",
            "hostname",
            ],
        "snapshot":snapshotId
        }

    output = ipf.post(url=EndPoint, json=Payload)
    config_hash = json.loads(output.text)['data']

    # iterated through config hash values and if the hostname for the hash is in the
    # original device list, add the hash to the list
    for var in config_hash:
        if var['hostname'] in tmp_device_hash:
            tmp_device_hash[var['hostname']] = var['hash']

    # as hostnames in IPFabric are returned with the DNS suffix, we want to strip that
    # to make it easier, we do this into a new dict
    device_hash = dict()

    for var in tmp_device_hash:
        hostname = var.split('.')[0].lower()
        device_hash[hostname] = tmp_device_hash[var]

    # get the config files

    device_configs = dict()

    print ('Getting Configs;')
    for device in device_hash:
        print (' > {}'.format(device))
        EndPoint = "/tables/management/configuration/download?hash={}".format(device_hash[device])
        # If not config is found for the device, the get will fail
        try:
            output = ipf.get(EndPoint)
            device_configs[device] = {'config':output.text}
        except:
            print(f"no config found for this device")
            device_configs[device] = {'config':"NO CONFIG"}
    print ('All Configs Extracted\n\n')

    return device_configs

