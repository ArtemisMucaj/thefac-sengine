### thefac search engine

This project is based on elastic search

## Install ElasticSearch

# .deb file here :

    - https://www.elastic.co/downloads/elasticsearch
    - sudo service elasticsearch start
    - sudo service elasticsearch status
    - curl -X GET http://localhost:9200 to verify that ElasticSearch is running

    check '/etc/elasticsearch' if there's any issue

# homebrew :

    - brew install elasticsearch
    - curl -X GET http://localhost:9200 to verify that ElasticSearch is running

    check '/usr/local/opt/elasticsearch/config/elasticsearch.yml'
    if there's any issue

## Setup

Create files/ folder and make sure "hpc.pdf" exists

elastic_interface.py line 25-26 rename if filename is not "hpc.pdf"

search.py line 26 : this is what we're looking for
