# Metadata ingestion from the space changes stream

With this example you process files coming form the space changes stream files and have their metadata automatically uploaded into Onedata.

In this simple example, the whole content of the file is attached as metadata of the file.

Before your run, please set all the variables in `.env` to correct values.

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
```

Now you can use web interface, oneclient or REST to upload the file ' `gamma_test_generated_200.hdf5`' and see that the `json` metadata filed in Onedata gets populated.

The ingestion process uses python library `fs-onedatfs` to access files located in your Onedata ecosystem and is used to ingest metadata.
