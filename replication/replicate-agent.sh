#!/usr/bin/env bash

usage() {
cat <<EOF
This script helps to preform data replication between two Oneproviders.

${0##*/} --oz <onezone url> { --sn <space name> | --sid <space id> } --sp <provider url or name> --dp <provider url or name>
         -t <token> [ --log-stream ] [ --save-seq ] [ --seq <change number> ] [ -env ]
Options:
  --dp               url or name of replicaton destination oneprovider
  -h, --help         display this help and exit
  --oz               onezone url
  --sid              instead of space name you can supply space id. space id takes precedence over --sn
  --seq              space change event sequence id from which you will start receiving events
  --save-seq         when the script is interputed, save the sequence number of last recieved event to the file ./last_seq
                     when starting the script try to read ./last_seq for the sequence number
  --log-stream        log raw stream of changes to stream.log
  --sn               space name
  --sp               url or name of replicaton source oneprovider
  -t                 onezone API token
  --env              try to get all needed parameters from the environment

Examples:

The simplest way to initalize the replication of data on space 'par-n-lis-c' from example providers 'krakow' to destination provider 'paris': 
${0##*/} --oz develop-onezone.develop.svc.dev.onedata.uk.to \\
                   --sp develop-oneprovider-paris.develop.svc.dev.onedata.uk.to \\
                   --dp develop-oneprovider-lisbon.develop.svc.dev.onedata.uk.to \\
                   --sn par-n-lis-c \\
         -t MDAxNWxvY2F0...

If user has 2 spaces named 'par-n-lis-c' the script will fail. The solution is to provider space id instead of space name:
${0##*/} --oz develop-onezone.develop.svc.dev.onedata.uk.to \\
                   --sp develop-oneprovider-paris.develop.svc.dev.onedata.uk.to \\
                   --dp develop-oneprovider-lisbon.develop.svc.dev.onedata.uk.to \\
                   --sid ced4b8030a033ee22eaad8c79fc519b1 \\
         -t MDAxNWxvY2F0....

By default script starts replication by monitoring latest changes in the space. You can controll it by providing seq number.
${0##*/} --oz develop-onezone.develop.svc.dev.onedata.uk.to \\
                   --sp develop-oneprovider-paris.develop.svc.dev.onedata.uk.to \\
                   --dp develop-oneprovider-lisbon.develop.svc.dev.onedata.uk.to \\
                   --sn par-n-lis-c \\
                   --seq 100 \\
         -t MDAxNWxvY2F0...

The above command will start replication process by getting all changes since the change numbered as 100.

To run a continous replication you can save the last received seq number upon scrip exit:
${0##*/} --oz develop-onezone.develop.svc.dev.onedata.uk.to \\
                   --sp develop-oneprovider-paris.develop.svc.dev.onedata.uk.to \\
                   --dp develop-oneprovider-lisbon.develop.svc.dev.onedata.uk.to \\
                   --sid ced4b8030a033ee22eaad8c79fc519b1 \\
                   --save-seq \\
         -t MDAxNWxvY2F0...

When run next time, above command will read the last sequence number from the file ./last_seq.

You can provide most parameters also as exported variables. Create a file with content:

export  onezone_url="develop-onezone.develop.svc.dev.onedata.uk.to"
export  source_space_name="par-n-lis-c"
export  source_provider="develop-oneprovider-paris.develop.svc.dev.onedata.uk.to"
export  target_provider="develop-oneprovider-lisbon.develop.svc.dev.onedata.uk.to"
export  api_token="MDAxNWxvY2F00aW9uIG9uZXpvbmUKMDAzMGlkZW500aWZpZXIgN2YwMGU1ODkwYzg5ZjAyYjhhMmE3YWVhMjc00NDhjOTkKMDAxYWNpZCB00aW1lIDwgMTU1MTM1NTY5NwowMDJmc2lnbmF00dXJlIAXeTetBfdvGydV5TGrJynEeaQgMgS7LH1IUPeti700qXCg"

and source it. Make sure your variables are present in env. You can now run replication using command:
${0##*/} --env

EOF
exit 1
}

strip_url() { 
  local url=$1
  url=${1#https://}
  url=${url#http://}
  url=${url#www.}
  url=${url%%/*}
  echo "$url"
}

main() {

  if (( ! $# )); then
    usage
  fi

  # Default values
  seq_save=0
  log_stream=0

  while (( $# )); do
      case $1 in
          -h|-\?|--help)   # Call a "usage" function to display a synopsis, then exit.
              usage
              exit 0
              ;;
          --env)
              ;;
          --oz)
              onezone_url=$(strip_url "$2")
              shift
              ;;
          --dp)
              target_provider=$(strip_url "$2")
              shift
              ;;
          --sp)
              source_provider=$(strip_url "$2")
              shift
              ;;
          --sid)
              source_space_id=$2
              shift
              ;;
          --seq)
              last_seq_number=$2
              shift
              ;;
          --seq-save)
              seq_save=1
              shift
              ;;
          --log-stream)
              log_stream=1
              shift
              ;;
          --sn)
              source_space_name=$2
              shift
              ;;
          -t)
              api_token=$2
              shift
              ;;
          -?*|*)
              printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
              exit 1
              ;;
      esac
      shift
  done


  ###
  # Parameters validation
  ##

  errors=0;
  # On 17 line, port change port to 8443
  if [[ -z ${onezone_url+x} ]]; then
    echo "ERROR: Missign onezone url." ;
    errors=1
  else
    onezone_url="https://$onezone_url" 
  fi

  if [[ -z ${source_space_name+x} && -z ${source_space_id+x} ]]; then
    echo "ERROR: You must supply space name or space id." 
    errors=1
  fi

  if [[ -z ${source_provider+x} ]]; then
    echo "ERROR: Missign source provider name or url." ;
    errors=1
  fi

  if [[ -z ${source_provider+x} ]]; then
    echo "ERROR: Missign target provider name or url." ;
    errors=1
  fi

  if [[ -z ${source_provider+x} ]]; then
    echo "ERROR: Missign onezone api token." ;
    errors=1
  fi

  if (( errors )); then
    echo "Please see --help, study examples and supply needed parameters."
    exit 1
  fi

  # One curl command to rule them all
  _curl=(curl -k -N --tlsv1.2 --fail --show-error --silent -H "X-Auth-Token:$api_token")
  
  ###
  # If space name is supplied try to match find matching space id
  ##

  if [[ -z ${source_space_id+x} ]]; then
    all_spaces=$(${_curl[@]} "$onezone_url/api/v3/onezone/user/spaces" | jq -r '.spaces[]')

    matched_spaces=()
    for space_id in $all_spaces ; do
      space_name=$(${_curl[@]} "$onezone_url/api/v3/onezone/spaces/$space_id" | jq -r ".name")
      if [[ "$source_space_name" == "$space_name" ]]; then
        matched_spaces+=($space_name $space_id)
      fi
    done

    if [[ ${#matched_spaces[@]} -eq 0 ]]; then 
      echo "No space with name <$source_space_name> found in onezone <$onezone_url>"
      exit 1
    fi

    if [[ ${#matched_spaces[@]} -ge 3 ]]; then 
      echo "Found 2 or more spaces with name <$source_space_name> found in onezone <$onezone_url>:"
      for (( i = 0; i < ${#matched_spaces[@]}; i += 2 )); do
        printf 'Space name: <%s> , space id: <%s>\n' "${matched_spaces[i]}" "${matched_spaces[i+1]}"
      done
      echo "Cannot decide which one to use. Exiting."
      exit 1
    fi
    source_space_id=${matched_spaces[1]}
  fi

  ###
  # Using space id get space information and validate it against providers parameters
  ##

  read space_name space_id providers < <(${_curl[@]} "$onezone_url/api/v3/onezone/spaces/$source_space_id" | jq -r '.name,.spaceId,(.providers | to_entries[] | "\(.key):\(.value)" )' | tr  '\n' ' ') 

  cat <<EOF
  ┌──────────────────────────────────────────────────────────┐
  │ Information about space                                  │
  └──────────────────────────────────────────────────────────┘

EOF
  
  echo "    Space name: <$space_name>"
  echo "    Space id: <$space_id>"
  for provider in $providers; do
    IFS=':' read provider_id support_size <<<"$provider"
    read provider_name domain < <(${_curl[@]} "$onezone_url/api/v3/onezone/providers/$provider_id" | jq -r ".name,.domain" | tr  '\n' ' ')
    echo "    Provider <$provider_name>"
    echo "      with id <$provider_id>"
    echo "      domain url <$domain>"
    echo "      suppots space <$space_name> with storage size of <$support_size> bytes"

    if [[ "$source_provider" =~ "$domain" ]]; then
      source_provider_id="$provider_id" ;
    fi

    if [[ "$target_provider" =~ "$domain" ]]; then
      targert_provider_id="$provider_id" ;
    fi
  done
  echo ""

  if [[ -v ${targert_provider_id} ]]; then
    echo "ERROR: <$target_provider> did not match any of the providers that supports the space <$space_name>"
    exit 1
  fi

  if [[ -v ${source_provider_id} ]]; then
    echo "ERROR: <$source_provider> did not match any of the providers that supports the space <$space_name>"
    exit 1
  fi

  ###
  # Using space id get space information and validate it against providers parameters
  ##

  cat <<EOF
  ┌──────────────────────────────────────────────────────────┐
  │ Replication information                                  │
  └──────────────────────────────────────────────────────────┘

    Starting monitoring of changes of space <$space_name>, on provider <$source_provider>.
    All changess will be replicated to provider <$target_provider> that also supports space <$space_name>

EOF

  if [[ -z ${last_seq_number+x } ]]; then 
    if (( seq_save )); then
      if [[ -f ./last_seq ]]; then
        last_seq_number=$(cat ./last_seq)
      fi
    fi
  fi
  if [[ "$last_seq_number" != "" ]] ; then
    if [[ $last_seq_number =~ ^[0-9]+$ ]] ; then
        last_seq="last_seq=$last_seq_number"
        printf "    Requesting stream of changes from the event number <$last_seq_number>:\n\n"
    else
      echo "WARNING: Last sequence number <$last_seq_number> does not match regexp ^[0-9]+$, ommiting."
    fi
  else
       printf "    Subscribing to the steam of changes:\n\n"
  fi


  log_steam_cmd() { if (( log_stream )); then gstdbuf -i0 -o0 -e0 tee -a stream.log; else cat; fi; }

  _curl=(curl -k -N --tlsv1.2 --show-error --silent -H "X-Auth-Token:$api_token")
  while IFS=$'\t' read seq file_name file_path file_id ; do
    echo "Changed file: <$file_name>"
    echo "  change stream number: <$seq>"
    echo "  path: <$file_path>"
    echo "  id: <$file_id>"
    transfer=$(${_curl[@]} -H 'Content-type: application/json' -X POST "https://$source_provider/api/v3/oneprovider/replicas/$file_path?provider_id=$targert_provider_id" | jq -r ".transferId")
    echo "  replication transfer id: $transfer"
    echo ""
    if (( seq_save )); then
      (( seq++ ))
      echo "$seq" > last_seq
    fi
  done < <(${_curl[@]} "https://$source_provider/api/v3/oneprovider/changes/metadata/$space_id?${last_seq}" | log_steam_cmd | gstdbuf -i0 -o0 -e0 jq -r 'select((.deleted==false ) and (.changes.type=="REG")) | "\(.seq)\t\(.name)\t\(.file_path)\t\(.file_id)"' )

}

main "$@"