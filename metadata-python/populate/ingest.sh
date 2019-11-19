#!/usr/bin/env bash

export $(egrep -v '^#' .env | xargs)
python3 ../faust/producer.py