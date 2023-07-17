import json
import pandas as pd 
import html.parser as htmlparser
import traceback 


parser = htmlparser.HTMLParser()

data_list = []

with open('bfhs.har','r') as file :
    content = json.loads(file.read())


pages =  [item for item in content['log']['entries'] if 'https://www.bhfs.com/Templates/AjaxHandlers/PeopleSearchHandler.ashx' == item['request']['url'] ]

for page in pages : 
    try:
        items = json.loads(page['response']['content']['text'])['Items']
    except :
        pass
    for item in items :
        try: 
            data_list.append({
            'first_name' : item['Title'].split()[0],
            'last_name': item['Title'].split()[-1],
            'title': item['PeoplePositionTitle'],
            'email':parser.unescape(item['PeopleEmail'])
            })
        except :
            print(traceback.format_exc())
            breakpoint()

df = pd.DataFrame(data_list)
df.to_csv('bfhs.csv')
