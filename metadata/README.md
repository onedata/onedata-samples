# Metadata ingestion service stack

With this example you can upload `*.hdf5 files into Onedata and have their metadata automatically uploaded into Onedata.

Example files with metadata is `gamma_test_generated_200.hdf5`.

Before your run, please set all the variables in `.env` to correct values.

To run the example:

```bash
# Set valid Onedata parameters
vim .env

# Inspect the docker-compose before running
docker-compose config

# Start the metadata ingestion service stack
docker-compose up
```

Now you can use web interface, oneclient or REST to upload the file ' `gamma_test_generated_200.hdf5`' and see that the `json` metadata filed in Onedata gets populated.

The ingestion process uses python library `fs-onedatfs` to accss files located in your Onedata ecosystem and is used to ingest metadata.
