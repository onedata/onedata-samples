import requests
import json 

onezone_url="orzech-onezone.orzech.svc.dev.onedata.uk.to"
source_space_name="krk-plirw"
sourceProvider="orzech-oneprovider-krakow.orzech.svc.dev.onedata.uk.to"
source_oneprovider_version="18.02.0-rc13"
apiToken="MDAxNWxvY2F00aW9uIG9uZXpvbmUKMDAzMGlkZW500aWZpZXIgMWFhN2NiNmM3ZGIwN2NiMTU4MThjZjZkNDQ2Nzc4N2UKMDAxYWNpZCB00aW1lIDwgMTU4NDU3ODYwNQowMDJmc2lnbmF00dXJlIOq9svI4y007dTVSxTn601reaKnul02Io645bfJxQE02lriICg"
spaceId="8d3172c2c8739e48eb1156c968a57d90"
lastSeq=3578



with requests.Session() as session:
  session.headers.update({'X-Auth-Token': apiToken })
  url="https://{}/api/v3/oneprovider/changes/metadata/{}?timeout=60000&last_seq={}".format(sourceProvider,spaceId,lastSeq)

  response = session.get(url,verify=False,stream=True)
  #print(response.headers)
  lines = response.iter_lines()
  for line in lines:
    # filter out keep-alive new lines
    if line:
        decoded_line = line.decode('utf-8')
        print(json.loads(decoded_line))
  print(response.headers)
  #print(response.json())

  # while True:
  #   pass
  # resp = self.session.request('POST',
  #                           url,
  #                           data=self.body,
  #                           timeout=self.timeout,
  #                           stream=True,
  #                           auth=auth,
  #                           verify=self.verify)