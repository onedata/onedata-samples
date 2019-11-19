#!/usr/bin/env python3

import os, sys
import json 
import time

from fs.onedatafs import OnedataFS
from onedatacustom.metadataextractor import MetaDataExtractorHdf5

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

onezoneUrl=os.environ['ONEZONE_HOST']
sourceSpaceName=os.environ['SPACE_NAME']
apiToken=os.environ['ONECLIENT_ACCESS_TOKEN']
sourceProvider=os.environ['ONECLIENT_PROVIDER_HOST']
insecure=os.environ['ONECLIENT_INSECURE']

#Space id will be inferred from Onezone based on space name
spaceId="" #8d3172c2c8739e48eb1156c968a57d90"
lastSeq="0" #3578

# Connect to oneprovider with onedatafs
odfs = OnedataFS(sourceProvider, apiToken, insecure=True, force_proxy_io=True)
# Print list of user spaces 
print(odfs.listdir('/'))

# Try to infer the spade id from space name
with requests.Session() as session:
  session.headers.update({'X-Auth-Token': apiToken })
  url="https://{}/api/v3/onezone/user/spaces".format(onezoneUrl)
  response = session.get(url,verify=False)

  spaceId=""
  for space in response.json()['spaces']:
    url="https://{}/api/v3/onezone/spaces/{}".format(onezoneUrl,space)
    response = session.get(url,verify=False)
    if response.json()['name'] == sourceSpaceName:
      if spaceId=="":
        spaceId=response.json()['spaceId']
      else:
        print("Error more then 1 space of name={} exists in the provider {}".format(sourceSpaceName,sourceProvider))
        sys.exit(1)
  if spaceId=="":
    print("No space of name={} exists in the provider {}".format(sourceSpaceName,sourceProvider))
    sys.exit(1)
  print("Space name={} spaceId={}".format(sourceSpaceName,spaceId))

# Start listening the changes API
changesJSON='{ "fileMeta": { "fields": ["name", "type", "deleted"], "always": true }}'
with requests.Session() as session:
  session.headers.update({'X-Auth-Token': apiToken })
  session.headers.update({'content-type': 'application/json' })
  url="https://{}/api/v3/oneprovider/changes/metadata/{}?timeout=60000&last_seq={}".format(sourceProvider,spaceId,lastSeq)
  response = session.post(url,data=changesJSON,verify=False,stream=True)

  lines = response.iter_lines()
  for line in lines:
    if line:
        decoded_line = json.loads(line.decode('utf-8'))
        if decoded_line["fileMeta"]["changed"] and not decoded_line["fileMeta"]["deleted"]:
          filePath=decoded_line['filePath']#.decode('utf-8')
          if filePath.lower().endswith("hdf5"):
            start = time.time()
            fileHandle = odfs.openbin(filePath, 'r+')
            metadata=MetaDataExtractorHdf5(fileHandle).to_json()
            end = time.time()
            metadataExtractTime=(end - start)
            start = time.time()
            odfs.setxattr(filePath,"onedata_json",metadata)
            end = time.time()
            metadataSetOnedataFSTime=(end - start)
            accessType=odfs.getxattr(filePath,"org.onedata.access_type")
            print("File={}, Access type={}, Metadata extract time={}, Metadata set with OnedataFS={}".format(filePath,accessType,metadataExtractTime,metadataSetOnedataFSTime))
