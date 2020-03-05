#!/usr/bin/env python3

import os, sys, json, time
import threading, Queue, concurrent.futures

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# Disable warnings about red https
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Onedatafs for data access
from fs.onedatafs import OnedataFS

# CTA Extractor
from onedatacustom.metadataextractor import MetaDataExtractorHdf5

# Configure logging
import logging as l
l.basicConfig(level=l.INFO, format='%(message)s')

# Input parameters 
onezoneUrl=os.environ['ONEZONE_HOST']
sourceSpaceName=os.environ['SPACE_NAME']
apiToken=os.environ['ONECLIENT_ACCESS_TOKEN']
sourceProvider=os.environ['ONECLIENT_PROVIDER_HOST']
insecure=os.environ['ONECLIENT_INSECURE']
lastSeq=os.environ['LAST_SEQUENCE']

# Space id will be inferred from Onezone based on space name
spaceId=""

# Initialize a Queue for threads to communicate. 
# During tests the queue never reached size more then 10k
BUF_SIZE = 1000000
q = Queue.Queue(BUF_SIZE)

# Get spaceId from the space name
with requests.Session() as session:
  session.headers.update({'X-Auth-Token': apiToken })
  url="{}/api/v3/onezone/user/spaces".format(onezoneUrl)
  response = session.get(url,verify=False)

  for space in response.json()['spaces']:
    url="{}/api/v3/onezone/spaces/{}".format(onezoneUrl,space)
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

# Changes stream is consumed in a separate thread
class ChangesListener(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ChangesListener,self).__init__()
        self.target = target
        self.name = name

    def run(self):
      # Start listening the changes API
      changesJSON='{ "fileMeta": { "fields": ["name", "type", "deleted"], "always": true }}'
      while True:
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
                    q.put(filePath)
                    l.debug("Putting file {} to the queue".format(filePath))
      return

# Process items in the queue
def traverse(root_path):
  l.debug("Directory: {}".format(root_path))
  while True:
    if q.empty():
      time.sleep(1)
      print("No items in a queue.")
    else:
      with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        while not q.empty():
          executor.submit(processPath, q.get(), root_path)

# Process a single path
def processPath(path,root_path):
  try:
    if path.endswith('.hdf5'):
      wholeStart = time.time()
      l.debug("Opening file: {}".format(path))
      start = time.time() ; file = root_path.openbin(path,mode="r+") ; end = time.time() ; fileOpenTime=(end - start)
      fileName = file.path
      filePath = path
      l.debug("Getting size of file: {}".format(path))
      start = time.time() ; size = odfs.getinfo(fileName).size ; end = time.time() ; filegetInfoTime=(end - start)
      l.debug("Size of file {} is: {}".format(path,size))
      if size > 0:
        l.debug("Extracting metadata from file: {}".format(path))
        start = time.time() ; decoded_json = MetaDataExtractorHdf5(file).to_json() ; end = time.time() ; metadataExtractTime=(end - start)
        l.debug("Attaching metadata to: {}".format(path))
        start = time.time() ; odfs.setxattr(fileName,"onedata_json",json.dumps(decoded_json)) ; end = time.time() ; metadataSetOnedataFSTime=(end - start)
        start = time.time() ; file.close() ; end = time.time() ; fileCloseTime=(end - start)
        start = time.time() ; accessType=odfs.getxattr(fileName,b"org.onedata.access_type") ; end = time.time() ; getAccessTypeTime=(end - start)
        l.debug("File={}, Access type={}, Metadata extract time={}, Metadata set with OnedataFS={}".format(filePath,accessType,metadataExtractTime,metadataSetOnedataFSTime))
        jsonLog = {} ;
        jsonLog["file"] = fileName ; jsonLog["metadataExtrationTime"] = metadataExtractTime ; jsonLog["accessType"] = str(accessType) ; jsonLog["metadataSettingTime"] = metadataSetOnedataFSTime ;
        jsonLog['getAccessTypeTime'] = getAccessTypeTime ; jsonLog['filegetInfoTime'] = filegetInfoTime ; jsonLog['fileOpenTime'] = fileOpenTime ;  
        jsonLog['fileCloseTime'] = fileCloseTime ; 
        wholeEnd= time.time()
        jsonLog['wholeTime'] = wholeEnd - wholeStart 
        jsonLog['queueSize'] = q.qsize()
        l.info("jsonLog: {}".format(json.dumps(jsonLog)))
      else:
        start = time.time() ; file.close() ; end = time.time() ; fileCloseTime=(end - start)
        l.debug("size zero, omitting {}".format(file))
    else:
      l.debug("file does not match regex, omitting {}".format(path))
  except Exception as e:
    l.info(e)

# Initialize OnedataFS
odfs = OnedataFS(sourceProvider, apiToken, insecure=True, force_direct_io=True)
# Print list of user spaces 
l.debug(odfs.listdir('/'))
# Open the space
space = odfs.opendir('/{}'.format(sourceSpaceName))

# Start filling up the queue with files
p = ChangesListener(name='producer')
p.start()

# Process items in the queue
traverse(odfs)

# Close OnedataFS
l.info("Processing ended. Closing onedatafs.")
odfs.close()
sys.exit(0)