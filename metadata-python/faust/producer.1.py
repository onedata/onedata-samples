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
            bootstrap_servers=['http://localhost:9092'],
            api_version=(0, 10))
    except Exception as ex:
        print('Exception while connecting Kafka')
        print(ex)
    finally:
        return _producer


if __name__ == '__main__':
    kafka_producer = connect_kafka_producer()
    with requests.Session() as session:
      session.headers.update({'X-Auth-Token': apiToken })
      url="https://{}/api/v3/oneprovider/changes/metadata/{}?timeout=60000&last_seq={}".format(source_provider,source_space_id,first_change)

      response = session.get(url,verify=False,stream=True)
      #print(response.headers)
      lines = response.iter_lines()
      for line in lines:
        print(line)
        # filter out keep-alive new lines
        if line:
            decoded_line = line.decode('utf-8')
            record = json.loads(decoded_line)
            #posts_topic.put(MyModel(record["seq"],record["name"],record["file_path"],record["file_id"]))
            publish_message(kafka_producer, TOPIC, KEY, json.dumps(decoded_line))
            #print(json.loads(decoded_line))
      print(response.headers)


    if kafka_producer is not None:
        kafka_producer.close()