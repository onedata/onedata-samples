


import requests
import json 

onezone_url="r1902-onezone.r1902.svc.dev.onedata.uk.to"
source_space_name="krk-plirw-par-c"
sourceProvider="r1902-oneprovider-krakow.r1902.svc.dev.onedata.uk.to"
source_oneprovider_version="v19.02.1-beta1"
apiToken="MDAzN2xvY2F00aW9uIHIxOTAyLW9uZXpvbmUucjE5MDIuc3ZjLmRldi5vbmVkYXRhLnVrLnRvCjAwMzBpZGVudGlmaWVyIDEzYzE1Mjc4ZDRhMGI5ZTAwNjhmYjU3NDY1N2ExNGY3CjAwMWFjaWQgdGltZSA8IDE1OTYyNTkxOTgKMDAyZnNpZ25hdHVyZSAQP4QqwsDA02fLJ1Mi009KNzkoUETRTnffA02y6V6ScW5sQo"
spaceId="f6e81a4421196db901ca2470f028c48f"
lastSeq=0
requestYAML='{ "fileMeta": { "fields": ["name", "type", "deleted"], "always": true }}'

# This cell downloads a dataset needed for a demo to a local filesystem and used onedata-fs to copy it onto a space.
# This cell should be run once before a demo as a data preparation job.

import io
import os
from fs.onedatafs import OnedataFS

# Get configuration from the environment

# Connect to Oneprovider
odfs = OnedataFS(sourceProvider, apiToken, insecure=True, force_proxy_io=True)
space = odfs.opendir('/{}'.format(source_space_name))

# Copy data to a space
#current_directory_fs = OSFS(".")
odfs.listdir('.')
exit(0)

with requests.Session() as session:
  session.headers.update({'X-Auth-Token': apiToken })
  session.headers.update({'Content-Type': 'application/json'})
  url="https://{}/api/v3/oneprovider/changes/metadata/{}?timeout=60000&last_seq={}".format(sourceProvider,spaceId,lastSeq)
  print(url)
  response = session.post(url,verify=False,stream=True,data=requestYAML)
  lines = response.iter_lines()
  for line in lines:
    # filter out keep-alive new lines
    if line:
        decoded_line = line.decode('utf-8')
        print(json.loads(decoded_line))
  print(response.headers)