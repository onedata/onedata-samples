# Metadata ingestion service stack

With this example you can upload `*.hdf5` and `*.fz` files into Onedata and have their metadata automatically uploaded into Onedata.

Example files with metadata are located in the directory `files_with_metadata/`.

Before your run, please set all the variables in `envs` to correct values.

To run the example:

```bash
# Set valid Onedata parameters
vim envs

# Source the variables into the shell
source envs

# Inspect the docker-compose before running
docker-compose config

# Start the metadata ingestion service stack
docker-compose up
```

Now you can use web interface, oneclient or REST to upload the files form the `files_with_metadata/` and see that the `json` metadata filed in Onedata gets populated.

The ingestion service stack service stack consists of:

- oneclient container, which provides transparent access to files from which we want to extract metadata
- metadata-ingester container, which monitors changes stream of the space, requests the metadata extraction and uploads the metadata
- metadata-extractor container, listens for metadata requests and extracts metadata form files provided by oneclient container

*Oneclient* and *metadata-ingester* are provided by Onedata team, *metadata-extractor* is use-case type specific. 
Dedicated metadata-extractors should be developed by users and used instead of the *metadata-extractor* image provided in the example.

## Debugging

In rare cases when oneclient container is killed too sudden directory `/tmp/oneclient` on a host machine becomes a dead mount-point.
This prevents subsequent runs of ingestion service stack. To fix this, run as root or with sudo: `umount /tmp/onedata`.

## Advanced

### Inspect metadata as extended file attributes

While having docker-compose running. You can attach to oneclient container and inspect metadata as extended file attributes.

For example, assuming you have uploaded a file `Event2_tel1.hdf5` to a space named `krk-pirw-par-3-lis-n`:

```bash
root@66a5d02ed93e:/mnt/oneclient/krk-pirw-par-3-lis-n# getfattr -d -m -  /mnt/oneclient/krk-pirw-par-3-lis-n/Event1_tel2.hdf5
getfattr: Removing leading '/' from absolute path names
# file: mnt/oneclient/krk-pirw-par-3-lis-n/Event1_tel2.hdf5
onedata_json="{\"EventID\":\"UIDASDBN456\",\"TelescopeID\":\"AFX124\",\"CaptureDate\":\"2012-04-23T16:25:08\",\"trigger\":112456}"
org.onedata.access_type="proxy"
org.onedata.file_blocks="[##################################################]"
org.onedata.file_blocks_count="1"
org.onedata.file_id="/Event1_tel2.hdf5"
org.onedata.replication_progress="100%"
org.onedata.space_id="301ee60f64a1afca299d00d669c46a1b"
org.onedata.storage_id="d1e72b6f08a13132d73388aa7715e942"
org.onedata.uuid="Z3VpZCNjNWMzMzcxN2MwMzllYjliYjM4YmYzZjRjOWNiYTgwOSMzMDFlZTYwZjY0YTFhZmNhMjk5ZDAwZDY2OWM0NmExYg"
```

### Run with tmux

If you are familiar with [tmux](https://github.com/tmux/tmux) please see the `run_with_tmux.sh` file. Run this script to easily run metadata ingestion and observe all important logs files.
