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


def get_the_good_line_bbox_indice(lines_layout,lines_bbox):
    score = []
    for x in range(0,len(lines_bbox)):
        score.append(0)
        for y in range(0,len(lines_bbox[x])):
            score[x] += len(re.findall(" "+re.escape(lines_bbox[x][y])+" "," "+lines_layout+" "))

    indiceMax = 0
    maxScore = -1

    for x in range(0,len(score)):
        if score[x] > maxScore:
            maxScore = score[x]
            indiceMax = x
            pass
        pass
    return indiceMax



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

    # We find all the value of yMin
    yMin = re.findall("yMin=\"([^\"]*?)\"",page_bbox)

    # We remove doublet and we sort the list
    yMin_tmp = []
    for p in range(0,len(yMin)):
        isthere = False
        for j in range(0,len(yMin_tmp)):
            if yMin_tmp[j] == yMin[p]:
                isthere = True
                break
        if isthere == False:
            yMin_tmp.append(yMin[p])

    yMin_tmp.sort()
    yMin = list(yMin_tmp)

    lines_bbox = []
    # We get all the word with the same yMin value
    for p in range(0,len(yMin)):
        lines_bbox.append( re.findall("<word[^>]*yMin=\""+str(yMin[p])+"\"[^>]*>([^<]*)</word>",page_bbox) )
        pass


    cpt_number_line_in_table = 0
    table = {}
    list_frame = {}
    context = " "
    for line_iterator in range(0,len(lines_layout)):
        if lines_layout[line_iterator] != "":
            if should_add_the_line_to_table(lines_layout[line_iterator]):
                # We add the line to table
                table[cpt_number_line_in_table] = lines_layout[line_iterator]

                # We add the frame to the list_frame
                indice = get_the_good_line_bbox_indice(lines_layout[line_iterator],lines_bbox)

                list_coord_line = re.findall("<word xMin=\"([^>]*)\" yMin=\""+str(yMin[indice])+"\" xMax=\"([^>]*)\" yMax=\"([^>]*)\">[^<]*</word>",page_bbox)
                xMin = []
                xMax = []
                yMax = []
                for q in range(0,len(list_coord_line)):
                    xMin.append(float(list_coord_line[q][0]))
                    xMax.append(float(list_coord_line[q][1]))
                    yMax.append(float(list_coord_line[q][2]))
                xMin = min(xMin)
                xMax = max(xMax)
                yMax = max(yMax)

                xMin = xMin/float(page_width)
                yMin_current = float(yMin[indice])/float(page_height)
                xMax = xMax/float(page_width)
                yMax = yMax/float(page_height)
                list_frame[cpt_number_line_in_table] = str(xMin)+' '+str(yMin_current)+' '+str(xMax)+' '+str(yMax)
                cpt_number_line_in_table += 1

            else:
                # We add the line to the context
                context += " " + " ".join(lines_layout[line_iterator].split()) + " "

    for x in range(0,len(table)):
        table[x] += context

    json_text["table"] = table
    json_text["list_frame"] = list_frame

    return json.dumps(json_text)



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

    # The last page of pages_layout is empty
    for i in range(0,len(pages_layout)-1):
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
        page_path = "Image/"

        if i + 1 >= 100:
            page_path = page_path + "hpc-" + str(i + 1) + ".png"
        elif i + 1 >= 10:
            page_path = page_path + "hpc-0" + str(i + 1) + ".png"
        else:
            page_path = page_path + "hpc-00" + str(i + 1) + ".png"


        data = getTheJsonFromThePage(pages_layout[i],pages_bbox[i],i,page_path,base)


        # add to elasticsearch
        res = req.put("http://localhost:9200/pdf/page/"+base+str(i),data)
        print(res.content)

    # end of main
    pass

# main loop
if __name__ == '__main__':
    main()
