import scrapy
import requests
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem

class NortonrosefulbrightSpider(scrapy.Spider):
    name = 'nortonrosefulbright'
    allowed_domains = ['nortonrosefulbright.com']
    start_urls = ['http://nortonrosefulbright.com/']


    def __init__(self):
        self.start_urls = []
        self.collect_people_urls()

    def parse(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_css('firm','p.nrf-person-title::text')
        loader.add_css('title','p.nrf-person-title strong::text')
        loader.add_xpath('email','//a[@class="nrf-email-link"]/@aria-label')
        loader.add_xpath('linkedin','//h1/following-sibling::a[1]/@href')
        loader.add_xpath('bio','string(//h2[contains(text(),"Biography")]/following-sibling::div)')
        loader.add_css('image','img.nrf-profile-image::attr(src)')
        loader.add_xpath('office','//div[@class="nrf-person-details row"]//a[@class="nrf-inline-link"]/text()')
        if response.css('div#education p br') : 
            selected_schools = response.css('div#education p::text').getall()
            for school in selected_schools :
                if 'law' in school.lower() : 
                    loader.add_value('law_school',school)
                if 'univ' in school.lower() :
                    loader.add_value('undergraduate_school',school)

        loader.add_xpath('law_school','//div[@id="education"]//*[contains(text(),"law") or contains(text(),"Law")]/text()')
        if loader._values.get('law_school'):
            if loader._values.get('law_school')[0].split()[-1].isdigit():
                loader.add_xpath('law_school_graduation_year',loader._values['law_school'][0].split()[-1])
        loader.add_xpath('undergraduate_school','//div[@id="education"]//*[contains(text(),"univ") or contains(text(),"Univ") and not(contains(text(),"law") orcontains(text(),"Law"))]/text()')
        if loader._values.get('undergraduate_school'):
            if loader._values.get('undergraduate_school')[0].split()[-1].isdigit():
                loader.add_xpath('undergraduate_school_graduation_year',loader._values['undergraduate_school'][0].split()[-1])

        loader.add_value('firm_bio','https://www.nortonrosefulbright.com/en/about/our-firm')
        yield loader.load_item()


    def collect_people_urls(self):
        self.logger.info('start collecting people urls .')
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
        self.start_urls += [
            individual['clickUri'] for individual in response['results']
        ]
        self.logger.info('\n {} urls collected \n'.format(len(self.start_urls)))
        max_page = response['totalCount']//100
        for page in range(1,max_page+1):
            data['firstResult'] = str(page*100)
            response = session.post('https://www.nortonrosefulbright.com/coveo/rest/search/v2', headers=headers, params=params, data=data).json()
            self.start_urls += [
                individual['clickUri'] for individual in response['results']
            ]
            self.logger.info('\n {} urls collected \n'.format(len(self.start_urls)))
        