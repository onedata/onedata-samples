#!/usr/bin/env python3
import faust

import requests
import json 
# from faust.app.base import BootStrategy
# class App(faust.App):
#     class BootStrategy(BootStrategy):
#          enable_kafka = False




app = faust.App('meta',
    version=1,
    topic_partitions=1,
)

class MyModel(faust.Record):
    seq: int
    name: str
    file_path: str
    file_id: str

#{'seq': 6680, 'name': 'gamma_test_generated_11143.hdf5', 'file_path': '/krk-plirw/samples_42001/space/1/1/gamma_test_generated_11143.hdf5', 'file_id': '000000000046426067756964233763623939373365356338353130663937663832313262316665626564616339233864333137326332633837333965343865623131353663393638613537643930', 'deleted': False, 'changes': {'xattrs': {'onedata_json': {'foo': 'bar'}}, 'version': 0, 'uid': '0c21c79fb35270d308b3c57895f607ac', 'type': 'REG', 'size': 6144, 'scope': '8d3172c2c8739e48eb1156c968a57d90', 'mtime': 1552929211, 'mode': 420, 'is_scope': False, 'ctime': 1553053207, 'atime': 1553042690}} 

posts_topic = app.topic('posts', value_type=str)
word_counts = app.Table('word_counts', default=int,
                        help='Keep count of words (str to int).')


@app.agent(posts_topic)
async def process(stream):
    #global page_views
    async for event in stream:
        print(f'Received: {event}')
        word_counts['0'] += 1

@app.page('/count/')
async def get_count(web, request):
    global page_views
    return web.json({
        "page_views": str(word_counts['0']),
    })

@app.agent(posts_topic)
async def producer(stream):

# @app.timer(1.0)
# async def populate():
#     await channel.put(MyModel(303))

if __name__ == '__main__':
    app.main()
    

