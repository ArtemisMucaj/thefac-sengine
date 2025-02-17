# Use requests to talk to elasticsearch
# based on : http://docs.python-requests.org/
# for http requests

import requests as req
import json


def format_results(results):
    data = [doc for doc in results['hits']['hits']]
    for doc in data:
        print("score : %s, pageNumber : %s" % (doc['_score'], doc['_source']['pageNumber']))


def main():
    # request elastic search
    # localhost:9200
    response = req.get('http://localhost:9200')
    print(str(response.headers))
    print(str(response.content))

    # query
    query = json.dumps({
        "query" : {
            "bool" : {
                "must" : [
                    {
                        "multi_match" : {
                            "query" : "spur gear",
                            "fields" : [ "table.*" ],
                            "operator":   "and"
                        }
                        # "query_string": {
                        #     "query" : "table.\*:(44 AND 46 AND 20)",
                        #     "use_dis_max" : "false",
                        #     "minimum_should_match" : "100%"
                        # }
                    }
                    ,
                    {
                        "match" : {
                            "content" : "spur gear"
                        }
                    }
                    ,
                    {
                        "match" : {
                            "brand" : "hpc"
                        }
                    }
                ],
                "must_not" : [],
                "should" : []
            }
        }
    })
    print(query)

    # search in localhost:9200/parts/hpc/_search
    # shows 10 first results order by _score
    res = req.get("http://localhost:9200/pdf/page/_search",data=query)

    output = json.loads(res.text)

    format_results(output)

    # end of main
    pass

# main loop
if __name__ == '__main__':
    main()
    pass
