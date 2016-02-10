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

def should_add_the_line_to_table(line):
    #On garde les lignes ou il y au moins la moitier de chiffres
    line = miner_keepOnlyNumericLine(line)

    #On garde les lignes avec au moins 3 colonnes
    line = miner_keepOnlyThreeAndMoreColumnsLine(line)
    if line != "":
        return True
    else:
        return False


def getTheJsonFromThePage(page_layout,page_bbox,page_number,image_path,brand):
    # The field of a page object in elasticsearch
    json_text = {}
    json_text["context"] = ""
    json_text["table"] = {}
    json_text["list_frame"] = {}
    json_text["page_number"] = page_number
    json_text["image_path"] = image_path
    json_text["brand"] = brand


    lines_layout = re.split('\n',page_layout)
    tmp_page_dimension = re.findall("<page width=\"([^\"]*)\" height=\"([^\"]*)\">",page_bbox)
    page_width = tmp_page_dimension[0][0]
    page_height = tmp_page_dimension[0][1]

    cpt_number_line_in_table = 0
    table = {}
    list_frame = {}
    for line_iterator in range(0,len(lines_layout)):
        if lines_layout[line_iterator] != "":
            if should_add_the_line_to_table(lines_layout[line_iterator]):
                # We add the line to table
                table[cpt_number_line_in_table] = lines_layout[line_iterator]

                # We add the frame to the list_frame
                words = re.split(' *',lines_layout[line_iterator])
                tmp_words = []
                for word_iterator in range(0,len(words)):
                    if words[word_iterator] != '':
                        tmp_words.append(words[word_iterator])
                words = list(tmp_words)
                xMin = 0
                yMin = 0
                xMax = 0
                yMax = 0
                print "$$$$$$$$$$ : ",line_iterator,words
                if len(words) >= 2:
                    current_line_bbox = re.findall("<word[^<>]*>"+words[0]+"<.*>"+words[len(words)-1]+"</word>",page_bbox,re.DOTALL)
                if len(words) == 1:
                    current_line_bbox = re.findall("<word[^<>]*>"+words[0]+"</word>",page_bbox,re.DOTALL)
                if current_line_bbox != []:
                    current_line_bbox = current_line_bbox[0]
                    print "           : ",current_line_bbox
                    xMin = float(min(re.findall("xMin=\"([^\"]*?)\"",current_line_bbox)))/float(page_width)
                    yMin = float(min(re.findall("yMin=\"([^\"]*?)\"",current_line_bbox)))/float(page_height)
                    xMax = float(max(re.findall("xMax=\"([^\"]*?)\"",current_line_bbox)))/float(page_width)
                    yMax = float(max(re.findall("yMax=\"([^\"]*?)\"",current_line_bbox)))/float(page_height)
                list_frame[cpt_number_line_in_table] = str(xMin)+' '+str(yMin)+' '+str(xMax)+' '+str(yMax)
                cpt_number_line_in_table += 1
            else:
                # We add the line to the context
                json_text["context"] += " ".join(lines_layout[line_iterator].split())

    json_text["table"] = table
    json_text["list_frame"] = list_frame

    # return json.dumps(json_text)
    return json_text


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
        print(str(filename)+":"+base64.b64encode(base+".html")+" already added to elasticsearch")
        # return 0
    else:
        print("pdftotext is running ...")
        sp.call(["pdftotext","-layout",filename, "./files/"+base64.b64encode(base)])

    if os.path.isfile("./files/"+base64.b64encode(base+".html")):
        print(str(filename)+":"+base64.b64encode(base+".html")+" already added to elasticsearch")
        # return 0
    else:
        print("pdftotext is running ...")
        sp.call(["pdftotext","-bbox",filename, "./files/"+base64.b64encode(base+".html")])


    # We open the bbox file
    f = open("./files/"+base64.b64encode(base+".html"),'r')
    content = f.read()
    f.close()

    inside_doc_flag = re.findall('<doc>(.*)</doc>',content,re.DOTALL)
    pages_bbox = re.findall('<page.*?</page>',inside_doc_flag[0],re.DOTALL)

    # We open the layout file
    f = open("./files/"+base64.b64encode(base),'r')
    content = f.read()
    f.close()
    pages_layout = re.split('\f',content)

    # save a page json object
    # {
    #   "filePath" : "hpc.pdf",
    #   "pageNumber": 1,
    #   "content" : " ... ",
    #    ...
    # }
    for i in range(43,len(pages_layout)):
        # page = pages[i]

        # # build json Object
        # text = " ".join(page.split())

        # json_text = {}
        # json_text["content"] = text
        # json_text["pageNumber"] = i
        # json_text["filepath"] = os.path.abspath(filename)



        # #On garde les lignes ou il y au moins la moitier de chiffres
        # page_tmp = miner_keepOnlyNumericLine(page)

        # #On garde les lignes avec au moins 3 colonnes
        # page_tmp = miner_keepOnlyThreeAndMoreColumnsLine(page_tmp)
        # lines = page_tmp.split('\n')

        # table = {}
        # for x in range(0,len(lines)):
        #     table[str(x)] = lines[x]
        #     pass

        # json_text["table"] = table
        # json_text["brand"] = base
        # data = json.dumps(json_text)

        data = getTheJsonFromThePage(pages_layout[i],pages_bbox[i],i,"/dummy/path",base)

        print pages_layout[i]
        print "###########"
        print data["table"]
        print "###########"
        print data["context"]
        print "###########"
        print data["list_frame"]

        exit(1)

        # add to elasticsearch
        res = req.put("http://localhost:9200/pdf/page/"+base+str(i),data)
        print(res.content)

    # end of main
    pass

# main loop
if __name__ == '__main__':
    main()
