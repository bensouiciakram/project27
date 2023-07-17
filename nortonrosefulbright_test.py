import requests

people_urls = []


session = requests.Session()

token = requests.get('https://www.nortonrosefulbright.com/coveo/rest/token').json()['token']


headers = {
    'authority': 'www.nortonrosefulbright.com',
    'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
    'authorization': 'Bearer {}'.format(token),
    'content-type': 'application/x-www-form-urlencoded; charset="UTF-8"',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
    'sec-ch-ua-platform': '"Linux"',
    'accept': '*/*',
    'origin': 'https://www.nortonrosefulbright.com',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.nortonrosefulbright.com/en/people',
    'accept-language': 'en-US,en;q=0.9',
}

params = (
    ('sitecoreItemUri', 'sitecore://web/{D4EFC18B-4C81-4F50-ABA5-B701ABEA9C61}?lang=en&amp;ver=2'),
    ('siteName', 'NRFWeb'),
    ('authentication', ''),
)

data = {
  '$actionsHistory': '[{"name":"Query","time":"\\"2021-09-12T19:17:27.548Z\\""}]',
  'referrer': 'https://www.nortonrosefulbright.com/en',
  'visitorId': '',
  'isGuestUser': 'false',
  'aq': '(NOT @z95xtemplate==ADB6CA4F03EF4F47B9AC9CE2BA53FF97) (@templateid=="17d44a53-c69f-45f4-ad0b-7d823823addf" $qre(expression: \'@languages = en\', modifier: \'40\'))',
  'cq': '((@z95xlanguage=="en")) ((@z95xlatestversion==1) (@source==Coveo_web_index_PROD_10))',
  'searchHub': 'people',
  'locale': 'en',
  'maximumAge': '900000',
  'firstResult': '0',
  'numberOfResults': '100',
  'excerptLength': '200',
  'enableDidYouMean': 'true',
  'sortCriteria': 'fieldascending',
  'sortField': '@cvpositionpriority',
  'queryFunctions': '[]',
  'rankingFunctions': '[]',
  'groupBy': '[{"field":"@location","maximumNumberOfValues":6,"sortCriteria":"occurrences","injectionDepth":4500,"completeFacetWithStandardValues":true,"allowedValues":[],"advancedQueryOverride":"(NOT @z95xtemplate==ADB6CA4F03EF4F47B9AC9CE2BA53FF97) (@templateid==\\"17d44a53-c69f-45f4-ad0b-7d823823addf\\" $qre(expression: \'@languages = en\', modifier: \'40\'))","constantQueryOverride":"((@z95xlanguage==\\"en\\")) ((@z95xlatestversion==1) (@source==Coveo_web_index_PROD_10))"},{"field":"@keyindustries","maximumNumberOfValues":7,"sortCriteria":"alphaascending","injectionDepth":4500,"completeFacetWithStandardValues":true,"allowedValues":[],"advancedQueryOverride":"(NOT @z95xtemplate==ADB6CA4F03EF4F47B9AC9CE2BA53FF97) (@templateid==\\"17d44a53-c69f-45f4-ad0b-7d823823addf\\" $qre(expression: \'@languages = en\', modifier: \'40\'))","constantQueryOverride":"((@z95xlanguage==\\"en\\")) ((@z95xlatestversion==1) (@source==Coveo_web_index_PROD_10))"},{"field":"@practiceareas","maximumNumberOfValues":6,"sortCriteria":"occurrences","injectionDepth":1000,"completeFacetWithStandardValues":true,"allowedValues":[],"advancedQueryOverride":"(NOT @z95xtemplate==ADB6CA4F03EF4F47B9AC9CE2BA53FF97) (@templateid==\\"17d44a53-c69f-45f4-ad0b-7d823823addf\\" $qre(expression: \'@languages = en\', modifier: \'40\'))","constantQueryOverride":"((@z95xlanguage==\\"en\\")) ((@z95xlatestversion==1) (@source==Coveo_web_index_PROD_10))"},{"field":"@position","maximumNumberOfValues":6,"sortCriteria":"occurrences","injectionDepth":1000,"completeFacetWithStandardValues":true,"allowedValues":[],"advancedQueryOverride":"(NOT @z95xtemplate==ADB6CA4F03EF4F47B9AC9CE2BA53FF97) (@templateid==\\"17d44a53-c69f-45f4-ad0b-7d823823addf\\" $qre(expression: \'@languages = en\', modifier: \'40\'))","constantQueryOverride":"((@z95xlanguage==\\"en\\")) ((@z95xlatestversion==1) (@source==Coveo_web_index_PROD_10))"}]',
  'retrieveFirstSentences': 'true',
  'timezone': 'Africa/Algiers',
  'enableQuerySyntax': 'false',
  'enableDuplicateFiltering': 'false',
  'enableCollaborativeRating': 'false',
  'debug': 'false',
  'allowQueriesWithoutKeywords': 'true'
}

response = session.post('https://www.nortonrosefulbright.com/coveo/rest/search/v2', headers=headers, params=params, data=data).json()
people_urls += [
    individual['clickUri'] for individual in response['results']
]
max_page = response['totalCount']//100
for page in range(1,max_page+1):
    data['firstResult'] = str(page*100)
    response = session.post('https://www.nortonrosefulbright.com/coveo/rest/search/v2', headers=headers, params=params, data=data).json()
    people_urls += [
        individual['clickUri'] for individual in response['results']
    ]
    print(len(people_urls))

breakpoint()
breakpoint()
#NB. Original query string below. It seems impossible to parse and
#reproduce query strings 100% accurately so the one below is given
#in case the reproduced version is not "correct".
# response = requests.post('https://www.nortonrosefulbright.com/coveo/rest/search/v2?sitecoreItemUri=sitecore%3A%2F%2Fweb%2F%7BD4EFC18B-4C81-4F50-ABA5-B701ABEA9C61%7D%3Flang%3Den%26amp%3Bver%3D2&siteName=NRFWeb&authentication', headers=headers, data=data)
