#!/usr/bin/env bash

ADMIN_PASSWORD=$1
PROVIDER_TO_DELETE_FQDN=$2
DOMAIN_NAME=$3

# Delete domain
while read id ; do 
  curl  -u "admin:$ADMIN_PASSWORD" "https://$DOMAIN_NAME/api/v3/onezone/providers/$id" ; 
done < <(curl -Ssk -u admin:$ADMIN_PASSWORD -X GET https://$DOMAIN_NAME/api/v3/onezone/providers | jq -r '.providers[]') \
        | jq . \
        | grep -B 6 "$PROVIDER_TO_DELETE_FQDN"

# Check it's not there
while read id ; do
  curl  -u "admin:$ADMIN_PASSWORD" "https://$DOMAIN_NAME/api/v3/onezone/providers/$id" ;
done < <(curl -Ssk -u admin:$ADMIN_PASSWORD -X GET https://$DOMAIN_NAME/api/v3/onezone/providers | jq -r '.providers[]') \
      | jq . \
      | grep -B 6 "$PROVIDER_TO_DELETE_FQDN"