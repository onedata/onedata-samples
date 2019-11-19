#!/usr/bin/env bash

ADMIN_PASSWORD=$1
PROVIDER_TO_DELETE_FQDN=$2
DOMAIN_NAME="embl.tk"


# Delete domain
while read id ; do 
  curl  -u "admin:$ADMIN_PASSWORD" "https://$DOMAIN_NAME/api/v3/onezone/providers/$id" ; 
done < <(curl -Ssk -u admin:$ADMIN_PASSWORD -X GET https://$DOMAIN_NAME/api/v3/onezone/providers | jq -r '.providers[]') \
        | jq . \
        | grep -B 6 ".$DOMAIN_NAME" \
        | grep $PROVIDER_TO_DELETE_FQDN -B 6 \
        | grep providerId | tr -d '" ,' \
        | cut -d ':' -f2 \
        | xargs -I{} curl  -u "admin:$ADMIN_PASSWORD" -X DELETE "https://$DOMAIN_NAME/api/v3/onezone/providers/{}" ; 
        
#Check it's not there
while read id ; do
  curl  -u "admin:$ADMIN_PASSWORD" "https://$DOMAIN_NAME/api/v3/onezone/providers/$id" ;
done < <(curl -Ssk -u admin:$ADMIN_PASSWORD -X GET https://$DOMAIN_NAME/api/v3/onezone/providers | jq -r '.providers[]') \
      | jq . \
      | grep -B 6 ".$DOMAIN_NAME"