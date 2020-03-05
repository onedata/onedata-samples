# Metadata ingestion while traversing a space

With this example you will traverse the whole space directory tree and process each file, so it's content is attached as it's metadata.

Before your run:

* please set all the variables in `.env` to correct values.
* upload a few example text files to the space

To run the example:

```bash
# Set valid Onedata parameters
vim .env

# Inspect the docker-compose before running
docker-compose config

# Start the metadata ingestion
time docker-compose run all > meta.log

# Use this command to monitor how many files have been processed
cat meta.log | stdbuf -i0 -o0 -e0 grep jsonLog | sed -r 's/.*jsonLog(.*)}.*/\1}/g' |  cut -f 2- -d ':' |   jq " [.wholeTime] | add" | wc -l

# Use this command to see how much time took to process each directory
cat meta.log.log | stdbuf -i0 -o0 -e0 grep jsonLog | sed -r 's/.*jsonLog(.*)}.*/\1}/g' |  cut -f 2- -d ':' |   jq -r '"\(.listDirTime) \(.file)"'  | sort -k 1 -t ' ' -n | uniq -c -w 19
```

The ingestion process uses python library `fs-onedatfs` to access files located in your Onedata ecosystem and is used to ingest metadata.
