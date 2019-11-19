#!/usr/bin/env bash

usage() {
cat <<EOF
This script helps to preform metadata ingestion for data that has been imported into Onedata space.

${0##*/} --oz <onezone url> { --sn <space name> | --sid <space id> } -t <token> [ --log-stream ] [ --log-metadata ] [ --save-seq ] [ --seq <change number> ] [ -env ]

Options:
  -h, --help         display this help and exit
  --oz               onezone url
  --sn               space name
  --sid              instead of space name you can supply space id. space id takes precedence over --sn
  --seq              space change event sequence id from which you will start receiving events
  --seq-save         when the script is interputed, save the sequence number of last recieved event to the file ./last_seq
                     when starting the script try to read ./last_seq for the sequence number
  --cache-freq       how often should cache file be check for pending metadata ingestions (default: 2 seconds)
  --log-stream       log raw stream of changes to stream.log
  --log-metadata     log extracted metadata into metadata.log
  -t                 onezone API token
  --env              try to get all needed parameters from the environment
  --defer-time       how long (in seconds) to wait before scheduling metadata ingestion of a modified file since the last activity on it.
  --match            regexp of a file that should be matched for metadata ingestion
  --debug            additional data transfer information

Examples:

The simplest way to initalize the metadata ingestion on space 'par-n-lis-c' of all uploaded or imported files:
${0##*/} --oz develop-onezone.develop.svc.dev.onedata.uk.to \\
                   --sn par-n-lis-c \\
                   --match ".*\\.*" \\
                   -t MDAxNWxvY2F0...

By default script starts by monitoring latest changes in the space. You can controll it by providing seq number.
${0##*/} --oz develop-onezone.develop.svc.dev.onedata.uk.to \\
                   --sp develop-oneprovider-paris.develop.svc.dev.onedata.uk.to \\
                   --sn par-n-lis-c \\
                   --match ".*\\.*" \\
                   --seq 100 \\
                   -t MDAxNWxvY2F0...

The above command will start metadata ingestion process by getting all changes since the change numbered as 100.

To run a continous metadata ingestion you can save the last received seq number upon scrip exit:
${0##*/} --oz develop-onezone.develop.svc.dev.onedata.uk.to \\
                   --sp develop-oneprovider-paris.develop.svc.dev.onedata.uk.to \\
                   --sid ced4b8030a033ee22eaad8c79fc519b1 \\
                   --match ".*\\.*" \\
                   --save-seq \\
                   -t MDAxNWxvY2F0...

When run next time, above command will read the last sequence number from the file ./last_seq.

You can provide most parameters also as exported variables. Create a file with content:

export onezone_url="develop-onezone.develop.svc.dev.onedata.uk.to"
export source_space_name="par-n-lis-c"
export source_provider="develop-oneprovider-krakow.develop.svc.dev.onedata.uk.to"
export source_oneprovider_version="18.02.0-rc11"
export api_token="MDAxNWxvY2F00aW9uIG9uZXpvbmUKMDAzMGlkZW500aWZpZXIgYzFkZGRiNDg3NzE3YTVhOTEwYTQyNmVlNzk4NzEwMDEKMDAxYWNpZCB00aW1lIDwgMTU2ODAwNzI2NAowMDJmc2lnbmF00dXJlIJLX7vprmMAKA02drfPKK00YhpRXxS12M00iBIme7RSIxJYCg"

and source it. Make sure your variables are present in env. You can now run metadata ingestion using command:
${0##*/} --env

EOF
exit 1
}

aliases() {
  case $( uname -s ) in
    Linux)
          _stdbuf=stdbuf
          _date=date
          _awk=gawk
          ;;
    Darwin)
          _stdbuf=gstdbuf
          _date=gdate
          _awk=gawk
          ;;
  esac
}

strip_url() { 
  local url=$1
  url=${1#https://}
  url=${url#http://}
  url=${url#www.}
  url=${url%%/*}
  echo "$url"
}

command_exists() {
  command -v "$@" > /dev/null 2>&1
}

check_dependency() {
  if ! command_exists $1 ; then
    echo "Error: please install command: $1"
    exit 1
  fi
}

main() {

  if (( ! $# )); then
    usage
  fi

  # Default values
  seq_save=0
  log_stream=0
  log_metadata=0
  defer_time=180
  cache_scan_frequency=2
  debug=0
  declare -a matches=()

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
              ;;
          --cache-freq)
              cache_scan_frequency=$2
              shift
              ;;
          --log-stream)
              log_stream=1
              ;;
          --log-metadata)
              log_metadata=1
              ;;
          --match)
              matches+=("$2")
              shift
              ;;
          --sn)
              source_space_name=$2
              shift
              ;;
          --user)
              onezone_user=$2
              shift
              ;;
          --password)
              onezone_pasword=$2
              shift
              ;;
          -t)
              api_token=$2
              shift
              ;;
          --defer-time)
              defer_time=$2
              shift
              ;;
          --debug)
              debug=1
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

  if [[ -z ${api_token+x} ]]; then
      if [[ -z ${onezone_user+x} ]] || [[ -z ${onezone_pasword+x} ]]; then
        echo "ERROR: Neither onezone api token nor onezone username and password were provided." ;
        errors=1
      else
          echo "curl -k -N --tlsv1.2 --fail --show-error --silent -u $onezone_user:$onezone_pasword $onezone_url/api/v3/onezone/user/client_tokens | jq -r '.token'"
          api_token=$(curl -k -N --tlsv1.2 --fail --show-error -X POST -d '' --silent -u "$onezone_user:$onezone_pasword" "$onezone_url/api/v3/onezone/user/client_tokens" | jq -r '.token') ;
          if [[ "$api_token" == "" ]]; then
            echo "ERROR: Could not retrive Onezone API token using credentials: $onezone_user:$onezone_pasword." ;
            errors=1
          fi
      fi
      
  fi
  echo "$api_token"
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

  done
  echo ""

  if [[ -v ${source_provider_id} ]]; then
    echo "ERROR: <$source_provider> did not match any of the providers that supports the space <$space_name>"
    exit 1
  fi

  ###
  # Using space id get space information and validate it against providers parameters
  ##

  cat <<EOF
  ┌──────────────────────────────────────────────────────────┐
  │ Changes information                                      │
  └──────────────────────────────────────────────────────────┘

    Starting monitoring of changes of space <$space_name>, on provider <$source_provider>.
    All changes will trigger a querry for a metadata on a coresponding file located on physical storage,
    and following update of metadata of that file in Onedata space.

EOF

  cat <<EOF > .env
onezone_url=$onezone_url
source_space_name=$space_name
source_spacie_id=$space_id
source_provider_name=$provider_name
source_provider=$domain
source_provider_id=$provider_id
source_oneprovider_version=18.02.0-rc13
api_token=$api_token
EOF
  
}

aliases
check_dependency "jq"
check_dependency $_stdbuf
check_dependency $_date
check_dependency $_awk
main "$@"
