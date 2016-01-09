# Use requests to talk to elasticsearch
# based on : http://docs.python-requests.org/
# for http requests

import requests as req
import base64
import json
import subprocess as sp

import os

# To use Poppler C++ API (this is way too complicated though)
# import ctypes
# libname = "/usr/lib/x86_64-linux-gnu/libpoppler-glib.so.8"
# poppler = ctypes.cdll.LoadLibrary(libname)

def isThereATable(page):
    pageFormat = ""

    # 'A' == 65, 'Z' == 90, 'a' == 97, 'z' == 122, '0' == 48, '9' == 57
    for x in range(0,len(page)):
        if (65 <= ord(page[x]) and ord(page[x]) <= 90) or (97 <= ord(page[x]) and ord(page[x]) <= 122):
            # page[x] = 'a'
            pageFormat += 'a'
        else:
            if (48 <= ord(page[x]) and ord(page[x]) <= 57):
                # page[x] = '0'
                pageFormat += '0'
            else:
                pageFormat += page[x]

    # print pageFormat
    lines = pageFormat.split("\n")

    for x in range(1,len(lines)):
        if lines[x] != "" and lines[x] == lines[x-1]:
            return True

    return False



def main():
    # request elastic search
    # localhost:9200
    response = req.get('http://localhost:9200')
    print(str(response.headers))
    print(str(response.content))

    base = "mich"
    filename = "./files/"+base+".pdf"

    if os.path.isfile(filename):
        print("Looks like your setup is correct")
    else:
        print("Make sure files/ folder isn't empty")
        exit(0)

    if os.path.isfile("./files/"+base64.b64encode(base)):
        print(str(filename)+" already added to elasticsearch")
        exit(0)
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
        json_text["isThereATable"] = isThereATable(page)
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
    pass
