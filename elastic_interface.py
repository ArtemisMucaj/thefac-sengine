# Use requests to talk to elasticsearch
# based on : http://docs.python-requests.org/
# for http requests

import requests as req
import base64
import json
import subprocess as sp

import os
import re

# To use Poppler C++ API (this is way too complicated though)
# import ctypes
# libname = "/usr/lib/x86_64-linux-gnu/libpoppler-glib.so.8"
# poppler = ctypes.cdll.LoadLibrary(libname)

def miner_lineIsNumeric(line):
    chars = list(line)
    cpt_numeric = 0
    cpt_other = 0
    for x in range(0,len(chars)):
        if chars[x].isdigit():
            cpt_numeric += 1
        elif chars[x] != " ":
            cpt_other += 1
        pass
    if cpt_numeric > cpt_other:
        return True
    else:
        return False

def miner_keepOnlyNumericLine(page):
    lines = re.split('\n',page)
    ans = ""
    for x in range(0,len(lines)):
        if miner_lineIsNumeric(lines[x]):
            ans += lines[x]
            ans += "\n"
        pass
    return ans

def miner_lineHaveThreeOrMoreColumns(line):
    list_elems = re.split(" {2,}",line);
    ans = 0
    for x in range(0,len(list_elems)):
        if list_elems[x] != '':
            ans += 1
            pass
        pass
    if ans >= 3:
        return True
    else:
        return False


def miner_keepOnlyThreeAndMoreColumnsLine(page):
    lines = re.split('\n',page)
    ans = ""
    for x in range(0,len(lines)):
        if miner_lineHaveThreeOrMoreColumns(lines[x]):
            ans += lines[x]
            ans += "\n"
        pass
    return ans


def main():
    # request elastic search
    # localhost:9200
    response = req.get('http://localhost:9200')
    print(str(response.headers))
    print(str(response.content))

    base = "hpc"
    filename = "./files/"+base+".pdf"

    if os.path.isfile(filename):
        print("Looks like your setup is correct")
    else:
        print("Make sure files/ folder isn't empty")
        exit(0)

    if os.path.isfile("./files/"+base64.b64encode(base)):
        print(str(filename)+" already added to elasticsearch")
        # return 0
    else:
        print("pdftotext is running ...")
        sp.call(["pdftotext","-layout",filename, "./files/"+base64.b64encode(base)])

    f = open("./files/"+base64.b64encode(base),"r")

    document = f.read()
    # get pages
    pages = document.split("\f")

    # save a page json object
    # {
    #   "filePath" : "hpc.pdf",
    #   "pageNumber": 1,
    #   "content" : " ... ",
    #    ...
    # }
    for i in range(len(pages)):
        page = pages[i]

        # build json Object
        text = " ".join(page.split())

        json_text = {}
        json_text["content"] = text
        json_text["pageNumber"] = i
        json_text["filepath"] = os.path.abspath(filename)



        #On garde les lignes ou il y au moins la moitier de chiffres
        page_tmp = miner_keepOnlyNumericLine(page)

        #On garde les lignes avec au moins 3 colonnes
        page_tmp = miner_keepOnlyThreeAndMoreColumnsLine(page_tmp)
        lines = page_tmp.split('\n')

        table = {}
        for x in range(0,len(lines)):
            table[str(x)] = lines[x]
            pass

        json_text["table"] = table
        json_text["brand"] = base
        data = json.dumps(json_text)

        # add to elasticsearch
        res = req.put("http://localhost:9200/pdf/page/"+base+str(i),data)
        print(res.content)

    # end of main
    pass

# main loop
if __name__ == '__main__':
    main()
