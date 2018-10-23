FROM ubuntu:bionic

MAINTAINER Michal Orzechowski <orzechowski.michal@gmail.com>

ARG VCS_REF
ARG BUILD_DATE

# Metadata
LABEL org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/onedata/onedata-samples/metadata" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.docker.dockerfile="/Dockerfile"

RUN apt-get update && apt-get install -y jq gawk curl
RUN mkdir /metadata 

WORKDIR /metadata

ADD ingestion-agent.sh /usr/local/bin/ingestion-agent.sh

ENTRYPOINT ["ingestion-agent.sh"]