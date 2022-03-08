import requests,sys
import json
from pprint import pprint

requests.packages.urllib3.disable_warnings()

#define IPFabric Objects

class obj_IPFabric:

    def __init__(self, servername, username, password):

        # perform inital API Authentication

        global serverName, snapshotId
        
        serverName = servername + '/api/v1/'
        snapshotId = '$last'
        authData = { 'username': username, 'password' : password }
        
        authEndpoint = serverName + 'auth/login'
        authPost = requests.post(authEndpoint, json=authData, verify=False)
        if not authPost.ok:
            print('Unable to authenticate: ' + authPost.text)
            sys.exit()

        # Collecting the accessToken 
        accessToken = authPost.json()['accessToken']

        # Creating the tokenHeaders

        global tokenHeaders 
        tokenHeaders = { 'Authorization' : 'Bearer ' + accessToken}
        

    def api_post (self, EndPoint_Short, Payload):

        # Module to make REST Posts
        EndPoint = serverName + EndPoint_Short
        
        req = requests.post(EndPoint, headers=tokenHeaders, json=Payload, verify=False)
        if not req.ok:
            print ("Error:")
            pprint(json.loads(req.text))
            sys.exit()
        return req
        

    def api_get (self, EndPoint_Short):

        # Module to make REST Posts

        EndPoint = serverName + EndPoint_Short
        
        req = requests.get(EndPoint, headers=tokenHeaders, verify=False)
        if not req.ok:
            print ("Error:")
            pprint(json.loads(req.text))
            sys.exit()
        return req       


    def api_patch (self, EndPoint_Short, Payload):

        # Module to make REST Posts

        EndPoint = serverName + EndPoint_Short
        
        req = requests.patch(EndPoint, headers=tokenHeaders, json=Payload, verify=False)
        if not req.ok:
            print ("Error:")
            pprint(json.loads(req.text))
            sys.exit()
        return req


    def get_configs(self, limit=5000):

        # return a list of devices using pre-defined filters for nxos and ios/ios-xe devices
        
        EndPoint = "tables/inventory/devices"
        Payload = { "columns":
                        ["hostname"],
                    "filters": {"and": [{"vendor": ["eq","cisco"]},{"or": [{"family": ["eq","ios"]},{"family": ["eq","ios-xe"]},{"family": ["eq","nx-os"]}]}]},
                    "pagination":
                        { "limit": limit,  "start": 0 },
                    "snapshot": snapshotId,
                    "reports": "/inventory/devices"
                    }
        
        output = self.api_post(EndPoint, Payload)
        
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

        output = self.api_post(EndPoint, Payload)
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
            try:
                output = self.api_get(EndPoint)
                device_configs[device] = {'config':output.text}
            except:
                device_configs[device] = {'config':"NO CONFIG"}
        print ('All Configs Extracted\n\n')

        return device_configs
    




    

    