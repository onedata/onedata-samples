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
if 'LAST_SEQUENCE' in os.environ:
  try:
    initialStartingSequence=int(os.environ['LAST_SEQUENCE'])
  except ValueError:
    initialStartingSequence=None
else:
  initialStartingSequence=None

# Number od worker threads
numberOfWorkers=3

# Space id will be inferred from Onezone based on space name
spaceId=""

myChangesListener = None

# Initialize a Queue for threads to communicate. 
# During tests the queue never reached size more then 10k
BUF_SIZE = 1000000
q = Queue.Queue(BUF_SIZE)

# Map translating random thread ids to sequential worker numbers
threadIdToWorkerNumberMap={}

# List of sequence number of each worker thread
threadsSequenceNumbers=[None]*numberOfWorkers

# List of filehandles for threads to save their state
fileHandles = []

# timmer
fileHandlesTimer = None

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
    def __init__(self, group=None, target=None, name=None, startingSequenceNumber=None,
                 args=(), kwargs=None, verbose=None):
        super(ChangesListener,self).__init__(target=target, name=name, verbose=verbose)
        self.args = args
        self.kwargs = kwargs
        self.startingSequenceNumber = startingSequenceNumber

    def run(self):
      # Start listening the changes API
      changesJSON='{ "fileMeta": { "fields": ["name", "type", "deleted"], "always": true }}'

      # Supply extra argument in the url if events should start from a designated sequence
      if self.startingSequenceNumber == None:
        urlTemplate = "https://{}/api/v3/oneprovider/changes/metadata/{}?timeout=60000"
      else:
        urlTemplate = "https://{}/api/v3/oneprovider/changes/metadata/{}?timeout=60000&last_seq={}"
      print(self.startingSequenceNumber,urlTemplate)
      while True:
        with requests.Session() as session:
          session.headers.update({'X-Auth-Token': apiToken })
          session.headers.update({'content-type': 'application/json' })
          url=urlTemplate.format(sourceProvider,spaceId,self.startingSequenceNumber)
          response = session.post(url,data=changesJSON,verify=False,stream=True)

          lines = response.iter_lines()
          for line in lines:
            if line:
                decoded_line = json.loads(line.decode('utf-8'))
                self.startingSequenceNumber = decoded_line["seq"]
                if decoded_line["fileMeta"]["changed"] and not decoded_line["fileMeta"]["deleted"]:
                  filePath=decoded_line['filePath']#.decode('utf-8')
                  if filePath.lower().endswith("hdf5"):
                    q.put([self.startingSequenceNumber,filePath])
                    l.debug("Putting file of seq={}, {} to the queue".format(self.startingSequenceNumber,filePath))
      return

# Process items in the queue
def traverse(root_path):
  l.debug("Directory: {}".format(root_path))
  while True:
    if q.empty():
      time.sleep(1)
      print("No items in a queue.")
    else:
      with concurrent.futures.ThreadPoolExecutor(max_workers=numberOfWorkers) as executor:
        while not q.empty():
          try:
            anItem=q.get()
            sequenceNumber = anItem[0]
            filePath = anItem[1]
            executor.submit(processPath, sequenceNumber, filePath, root_path)
          except KeyboardInterrupt:
            executor.shutdown(wait=False)
            myChangesListener.exit()
            if fileHandlesTimer: fileHandlesTimer.cancel()

# Process a single path
def processPath(sequenceNumber, path,root_path):
  try:
    threadId = threading.current_thread().ident
    if not threadId in threadIdToWorkerNumberMap:
      threadIdToWorkerNumberMap[threadId]=len(threadIdToWorkerNumberMap)
    #l.info("threadId={}, sequenceNumber={}, file={}".format(threadId,sequenceNumber,fileHandles[threadIdToWorkerNumberMap[threadId]]))
    threadsSequenceNumbers[threadIdToWorkerNumberMap[threadId]]=sequenceNumber

    if path.endswith('.json'):
      wholeStart = time.time()
      l.debug("Opening file: {}".format(path))
      start = time.time() ; file = root_path.open(path,mode="r") ; end = time.time() ; fileOpenTime=(end - start)
      fileName = file.name
      filePath = file
      l.debug("Getting size of file: {}".format(path))
      start = time.time() ; size = odfs.getinfo(fileName).size ; end = time.time() ; filegetInfoTime=(end - start)
      l.debug("Size of file {} is: {}".format(path,size))
      if size > 0:
        l.debug("Reading file: {}".format(path))
        start = time.time() ; decoded_json = json.loads(file.read()) ; end = time.time() ; metadataExtractTime=(end - start)
        l.debug("Attaching metadata to: {}".format(file))
        start = time.time() ; odfs.setxattr(fileName,"onedata_json",json.dumps(decoded_json)) ; end = time.time() ; metadataSetOnedataFSTime=(end - start)
        start = time.time() ; file.close() ; end = time.time() ; fileCloseTime=(end - start)
        start = time.time() ; accessType=odfs.getxattr(fileName,b"org.onedata.access_type") ; end = time.time() ; getAccessTypeTime=(end - start)
        l.debug("File={}, Access type={}, Metadata extract time={}, Metadata set with OnedataFS={}".format(filePath,accessType,metadataExtractTime,metadataSetOnedataFSTime))
        jsonLog = {} ;
        jsonLog["file"] = fileName ; jsonLog["metadataExtrationTime"] = metadataExtractTime ; jsonLog["accessType"] = str(accessType) ; jsonLog["metadataSettingTime"] = metadataSetOnedataFSTime ;
        jsonLog['getAccessTypeTime'] = getAccessTypeTime ; jsonLog['filegetInfoTime'] = filegetInfoTime ; jsonLog['fileOpenTime'] = fileOpenTime ;
        jsonLog['listDirTime'] = listDirTime ; jsonLog['isDirectoryTime'] = isDirectoryTime ; jsonLog['fileCloseTime'] = fileCloseTime ;
        wholeEnd= time.time()
        jsonLog['wholeTime'] = wholeEnd - wholeStart
        l.info("jsonLog: {}".format(json.dumps(jsonLog)))
      else:
        start = time.time() ; file.close() ; end = time.time() ; fileCloseTime=(end - start)
        l.debug("size zero, omitting {}".format(file))
    else:
      l.debug("file does not match regex, omitting {}".format(path))
  except Exception as e:
    print("ERRROR!")
    l.info(e)

# Ensure existence of structure of persistent direstories
statePersistencePath="./persistence/state"
if not os.path.exists(statePersistencePath):
    os.makedirs(statePersistencePath)

# If no starting sequence number was given try to get it from saved states
if initialStartingSequence == None:
  lowestSequenceNumber=None
  for stateFilePath in os.listdir(statePersistencePath):
    aFileHandle = open(os.path.join(statePersistencePath,stateFilePath),"r")
    try:
      # the file might be empty, corrupted, or content might not be a number
      savedSequence = int(aFileHandle.read())
    except ValueError:
      continue
    aFileHandle.close()
    if lowestSequenceNumber == None:
      lowestSequenceNumber = savedSequence
    else:
      if lowestSequenceNumber > savedSequence:
        lowestSequenceNumber = savedSequence

  initialStartingSequence = lowestSequenceNumber

# If values is None, then there were not files to load the saved state from
if initialStartingSequence != None:
  firstFileHandle = open(os.path.join(statePersistencePath,"{}.seq".format(0)),"w")
  # Save the state in case the script crashes early
  firstFileHandle.write(str(initialStartingSequence))
  firstFileHandle.close()

# Remove all the state files except the first
for stateFilePath in os.listdir(statePersistencePath):
  if stateFilePath != "0.seq":
    os.remove(os.path.join(statePersistencePath,stateFilePath))

for i in range(0,numberOfWorkers):
  # mode 'a' was chosen, not to overwrite the value of the '0.seq'
  fileHandles.append(open(os.path.join(statePersistencePath,"{}.seq".format(i)),"a"))

def flushFileHandles():
    for i in range(0,len(fileHandles)):
      aSequenceNumber=threadsSequenceNumbers[i]
      if aSequenceNumber != None:
        fileHandles[i].truncate(0)
        # temporary save of a sequence so the value does not change between write and when log message if printed
        fileHandles[i].write(str(aSequenceNumber))
        fileHandles[i].flush()
        l.info("Saving sequence={} of worker={} to file={}, ".format(threadsSequenceNumbers[i],i,fileHandles[i]))
    # TODO: fix it so that a task is scheduled properly!
    fileHandlesTimer = threading.Timer(2.0, flushFileHandles)
    fileHandlesTimer.start()

fileHandlesTimer = threading.Timer(2.0, flushFileHandles)
fileHandlesTimer.start()

# Initialize OnedataFS
odfs = OnedataFS(sourceProvider, apiToken, insecure=True, force_direct_io=True)
# Print list of user spaces 
l.debug(odfs.listdir('/'))
# Open the space
space = odfs.opendir('/{}'.format(sourceSpaceName))

# Start filling up the queue with files
myChangesListener = ChangesListener(name='producer',startingSequenceNumber=initialStartingSequence)
myChangesListener.start()

# Process items in the queue
traverse(odfs)

# Close OnedataFS
l.info("Processing ended. Closing onedatafs.")
odfs.close()

# Close workers filehandles
for i in range(0,numberOfWorkers):
  fileHandles[i].close()

sys.exit(0)