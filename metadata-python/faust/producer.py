import json
from random import random
from kafka import KafkaProducer
import requests
import os
onezone_url=os.environ['onezone_url']
source_space_name=os.environ['source_space_name']
source_space_id=os.environ['source_space_id']
source_provider_name=os.environ['source_provider_name']
source_provider=os.environ['source_provider']
source_provider_id=os.environ['source_provider_id']
source_oneprovider_version=os.environ['source_oneprovider_version']
api_token=os.environ['api_token']
first_change=os.environ['first_change']


TOPIC = 'test'
KEY = 'score'


def publish_message(producer_instance, topic_name, key, value):
    try:
        key_bytes = bytes(key, encoding='utf-8')
        value_bytes = bytes(value, encoding='utf-8')
        producer_instance.send(topic_name, key=key_bytes, value=value_bytes)
        producer_instance.flush()
        print('Message published successfully.')
    except Exception as ex:
        print('Exception in publishing message')
        print(ex)


def connect_kafka_producer():
    _producer = None
    try:
        # host.docker.internal is how a docker container connects to the local
        # machine.
        # Don't use in production, this only works with Docker for Mac in
        # development
        _producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            api_version=(0, 10))
    except Exception as ex:
        print('Exception while connecting Kafka')
        print(ex)
    finally:
        return _producer


if __name__ == '__main__':
    kafka_producer = connect_kafka_producer()
    with requests.Session() as session:
      session.headers.update({'X-Auth-Token': api_token })
      url="https://{}/api/v3/oneprovider/changes/metadata/{}?timeout=60000&last_seq={}".format(source_provider,source_space_id,first_change)

      response = session.get(url,verify=False,stream=True)
      print(url)
      print(response.headers)
      lines = response.iter_lines()
      for line in lines:
        print(line)
        # filter out keep-alive new lines
        if line:
            decoded_line = line.decode('utf-8')
            record = json.loads(decoded_line)
            #posts_topic.put(MyModel(record["seq"],record["name"],record["file_path"],record["file_id"]))
            message = {
                'index': record['seq'],
                #'value': record,
                'file_path': record['file_path'],
                'file_id': record['file_id'],
                'created': not(record['deleted']),
            }
            publish_message(kafka_producer, TOPIC, KEY, json.dumps(message))
    if kafka_producer is not None:
        kafka_producer.close()
        
#[2019-03-29 13:44:19,614: WARNING]: <Score: index=16440, value="{'seq': 16440, 'name': '2', 'file_path': '/krk-plirw/samples_42001/space/1/2', 'file_id': '0000000000464EF867756964236138316333623634663462373263653535316439373863363133363561653135233864333137326332633837333965343865623131353663393638613537643930', 'deleted': False, 'changes': {'xattrs': {}, 'version': 0, 'uid': '0c21c79fb35270d308b3c57895f607ac', 'type': 'DIR', 'size': 0, 'scope': '8d3172c2c8739e48eb1156c968a57d90', 'mtime': 1552929212, 'mode': 493, 'is_scope': False, 'ctime': 1553053207, 'atime': 1553830915}}">