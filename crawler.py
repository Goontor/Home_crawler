import requests
import pygal
import datetime
import re
from bs4 import BeautifulSoup
import lxml
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import splrep,splev


def home_spider_short(max_pages,residence_code):
    page =0
    main_url="http://www1.centadata.com/eptest.aspx?type=3&code=" + residence_code + "&info=tr&code2=&page="
    while page < max_pages :
        url=main_url+str(page)
        source_code=requests.get(url)
        plain_text= source_code.text
        soup=BeautifulSoup(plain_text)
        tag_list=[]
        data_list=[]
        extract= soup.find("form",{"id" : "fctmod1tab2"})
        first_div= extract.find("div",{"class" : "tabber"})
        data_table=first_div.findAll("table",{"title" : "Detail"})
        tag_div = extract.findAll("tr")[1].findAll("td")
        for input in tag_div:
            tag_list.extend(input.get("class"))
        for item in data_table:
            result_dico={}
            for tag in tag_list:
                result=item.find("td",{"class",tag})
                if result and len(result.contents)<=1:
                    result_dico[tag]=result.string
                else:
                    if result:
                        result_dico[tag] = result.contents
            data_list.append(result_dico)
        page+=1
    print(data_list)
    return (data_list)


def home_spider_all(residence_code,residence_type):
    site_url_start="http://txhist.centadata.com/tfs_centadata/Pih2Sln"
    site_url_end="&info=basicinfo&ci=en-us"
    main_url = site_url_start + "/TransactionHistory.aspx?type=" + residence_type + "&code=" + residence_code + site_url_end
    source_code = requests.get(main_url)
    plain_text= source_code.text
    soup=BeautifulSoup(plain_text,features="html.parser")
    link_block=soup.find("div",{"id":"unitTran-left"}).findAll("div",{"class":"divBldgName"})
    results=[]
    for key in link_block:
        if key.parent.get("href"):
            key_source_code = requests.get(site_url_start + "/" + key.parent.get("href") + site_url_end)
            key_plain_text = key_source_code.text
            key_soup = BeautifulSoup(key_plain_text, features="html.parser")
            key_table=key_soup.find("div",{"id":"unitTran-main"}).findAll("tr",{"class":"trHasTrans"})

            for data in key_table:
                output_dico = {}

                input_table=data.findAll("td")

                output_dico["sealable_area"]=input_table[0].string.replace(" ","").replace('"','').replace('\r','').replace('\n','').replace(',','')

                output_dico["gross_area"] = input_table[1].string.replace(" ", "").replace('"', '').replace('\r','').replace('\n','').replace(',','')
                if "M" in input_table[2].string:
                    output_dico["price"] = 1000000*float(input_table[2].string.replace(" ", "").replace('"', '').replace("M","").replace('\r','').replace('\n',''))
                else:
                    output_dico["price"] = 1000000 * float(
                        input_table[2].string.replace(" ", "").replace('"', '').replace("M", "").replace('\r','').replace('\n', '').replace(",",""))
                output_dico["date"]=datetime.datetime.strptime(input_table[3].find("input",{"class","hdfRegDate"}).get("value"),"%Y-%m-%d")

                results.append(output_dico)
    return results

def average_data_new(data_list):

    average_result = {}
    error_count=0
    previous_saleable=1
    previous_gross=1
    for data in data_list:
        print(data["sealable_area"])
        if not data["sealable_area"]=="-":
            num_value=data["price"]/float(data["sealable_area"])
        else:
            if float(data["gross_area"])==previous_gross:
                num_value=data["price"]/previous_saleable
            else:
                error_count+=1
            continue
        date=data["date"]
        if not date in average_result.keys():
            average_result[date]={"value" : num_value, "count" : 1}
        else:
            old_count =average_result[date]["count"]
            new_count = old_count + 1
            new_average=(average_result[date]["value"]*old_count+num_value)/new_count
            average_result[date]["value"] = new_average
            average_result[date]["count"] = new_count
        previous_saleable=float(data["sealable_area"])
        previous_gross = float(data["gross_area"])

    return average_result


def num_average_data(data_list):
    options="/".join(x.replace("tdtr1","") for x in data_list[0].keys())
    choice=input("What do you want to display? : "+options)
    average_result={}
    while True:
        print(data_list[0].keys())
        if "tdtr1"+choice in data_list[0].keys():

            break
        else:
            choice = input("Wrong input! Please chose among : " + options)
    for data in data_list:
        num_value=float(re.sub('[^0-9]+', '',data["tdtr1"+choice]))
        date=datetime.datetime.strptime(data["tdtr1reg"],"%d/%m/%y")
        if not date in average_result.keys():
            average_result[date]={"value" : num_value, "count" : 1}
        else:
            old_count =average_result[date]["count"]
            new_count = old_count + 1
            new_average=(average_result[date]["value"]*old_count+num_value)/new_count
            average_result[date]["value"] = new_average
            average_result[date]["count"] = new_count

    return average_result


def plot_average_data(data_list,smooth_factor):
    data=[]
    axis=[]
    previous_value=0
    count=0
    for key in sorted(data_list):
        num_value=float(data_list[key]["value"])
        if previous_value==0:
            previous_value=num_value
        if (num_value>(2-smooth_factor)*previous_value) or (num_value<smooth_factor*previous_value):
            print("pop : "+str(key))
            continue
        else:
            data.append(float(data_list[key]["value"]))
            axis.append(key)
            previous_value = num_value
        count+=1
    print(data)
    print(axis)

    pygraph= pygal.Line(title="Result",x_label_rotation=40,width=2000,x_labels_major_every=40,show_minor_x_labels=False)
    pygraph.add("data",data)
    pygraph.x_labels=axis
    pygraph.render_to_file(r"ressources\result.svg")

    for i in range(0,len(axis)):
        axis[i]=axis[i].timestamp()

    print(axis)
    plt.figure()
    bspl = scipy.interpolate.splrep(axis, data, s=5)
    bspl_y = scipy.interpolate.splev(axis, bspl)
    plt.plot(axis, data)
    plt.plot(axis, bspl_y)
    plt.show()
#list=num_average_data(home_spider_short(1,"XSHNIHSXHT"))
#plot_average_data(list)

list=average_data_new(home_spider_all("TNDTZHTRHT","3"))
plot_average_data(list,0.80)