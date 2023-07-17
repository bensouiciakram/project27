import json
import pandas as pd 
import html.parser as htmlparser
import traceback 


parser = htmlparser.HTMLParser()

data_list = []

with open('mto.har','r') as file :
    content = json.loads(file.read())


pages =  [item for item in content['log']['entries'] if 'https://www.mto.com/Templates/AjaxHandlers/LawyerSearchHandler.ashx' == item['request']['url'] ]

for page in pages : 
    try:
        items = json.loads(page['response']['content']['text'])['data']
    except :
        pass
    for item in items :
        try: 
            data_list.append({
            'first_name' : item['NodeTitle'].split()[0],
            'last_name': item['NodeTitle'].split()[-1],
            'title': item['PersonTitle'],
            'email':item['Email'],
            'office':item['Office']
            })
        except :
            print(traceback.format_exc())
            breakpoint()

df = pd.DataFrame(data_list)
df.to_csv('mto.csv')
