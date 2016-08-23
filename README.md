# thefac search engine
This project is based on elastic search

### .deb

    - https://www.elastic.co/downloads/elasticsearch
    - sudo service elasticsearch start
    - sudo service elasticsearch status
    - curl -X GET http://localhost:9200 to verify that ElasticSearch is running

    check '/etc/elasticsearch' if there's any issue

### homebrew :

    - brew install elasticsearch
    - curl -X GET http://localhost:9200 to verify that ElasticSearch is running

    check '/usr/local/opt/elasticsearch/config/elasticsearch.yml' if there's any issue
