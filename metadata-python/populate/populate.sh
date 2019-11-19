#!/usr/bin/env bash

space_name=krk-pirw
changes_log=/tmp/changes.log
kawka_dir=/Users/orzech/Dropbox/home/repos/onedata/kafka-docker

# Get all envs
get_envs() {
  ./envs.sh --sn $space_name  --oz rc13-onezone.rc13.svc.dev.onedata.uk.to --sp rc13-oneprovider-krakow.rc13.svc.dev.onedata.uk.to --user joe --password password
}

# Copy files to oneclient
copy_files() {
  docker-compose -f oneclient.yaml up -d
  ( docker-compose -f oneclient.yaml logs -f & ) | grep -q "Oneclient ready"
  docker cp samples_1000.tgz oneclient:/
  docker exec -it oneclient bash -c "cd / && tar zxvf samples_1000.tgz && ls -lR /samples_1000 | grep '\-\rw\-r\-\-r\-\-' | wc -l"
  docker exec -it oneclient bash -c "cp -Rnv /samples_1000 /mnt/oneclient/$space_name" 
  docker exec -it oneclient bash -c "ls -lR /mnt/oneclient/$space_name | grep '\-\rw\-r\-\-r\-\-' | wc -l"
}

get_changes(){
# Get whole changes stream
  export $(egrep -v '^#' .env | xargs)
  curl  --silent -k -N --tlsv1.2  -H "X-Auth-Token: $api_token"  "https://$source_provider/api/v3/oneprovider/changes/metadata/$source_space_id?last_seq=$1"
}

changes_stats() {
  echo "First change:"
  tmp_var="$(grep -n samples_1000 /tmp/changes.log | head -n1)"
  first_change_line=$(echo "$tmp_var" | cut -d ":" -f 1)
  first_change=$(echo "$tmp_var" | cut -d ':' -f 2- | jq '.seq')
  echo $first_change
  echo "first_change=$first_change" >> .env

  echo "Last change:"
  tmp_var="$(grep -n samples_1000 /tmp/changes.log |  tail -n1)"
  last_change_line=$(echo "$tmp_var" | cut -d ":" -f 1)
  last_change=$(echo "$tmp_var" | cut -d ':' -f 2- | jq '.seq')
  echo $last_change
  echo "last_change=$last_change" >> .env

  echo "Number of files changes:"
  sed -n $first_change_line,${last_change_line}p /tmp/changes.log | jq -c 'select(.changes.type == "REG")' | wc -l
  echo "Number of dirs changes:"
  sed -n $first_change_line,${last_change_line}p /tmp/changes.log | jq -c 'select(.changes.type == "DIR")' | wc -l

  echo "Number of files:"
  sed -n $first_change_line,${last_change_line}p /tmp/changes.log | jq -c 'select(.changes.type == "REG") | .file_path' | sort | uniq -c | wc -l
  echo "Number of dirs:"
  sed -n $first_change_line,${last_change_line}p /tmp/changes.log | jq -c 'select(.changes.type == "DIR") | .file_path' | sort | uniq -c | wc -l
}
# sed -n $first_change_line,${last_change_line}p /tmp/changes.log | jq '.file_path' | sort | uniq -c 

start_kafka() {
  #docker rm -f $(docker ps -aq)
  docker-compose --project-directory $kawka_dir -f $kawka_dir/docker-compose-single-broker.yml rm -fsv
  docker-compose --project-directory $kawka_dir -f $kawka_dir/docker-compose-single-broker.yml up --force-recreate 
}

export $(egrep -v '^#' .env | xargs)
# get_envs
# copy_files
# get_changes > $changes_log
# get_changes $first_change
#changes_stats
start_kafka

