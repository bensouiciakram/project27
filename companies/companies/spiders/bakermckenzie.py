import scrapy
from scrapy import Request
import chompjs
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall

class BakermckenzieSpider(scrapy.Spider):
    name = 'bakermckenzie'
    allowed_domains = ['bakermckenzie.com']
    start_urls = ['https://bakermckenzie.com/']

    def __init__(self):
        self.people_template = 'https://www.bakermckenzie.com/en/people/?skip={}&sort=2&reload=false&scroll=242'


    def start_requests(self):
        yield Request(
            self.people_template.format(24),
            callback = self.parse_total
        )
    

    def parse_total(self,response):
        data = self.get_data(response)
        yield Request(
            self.people_template.format(data['ResultCount']),
            callback = self.parse_results
        )
    

    def parse_results(self,response):
        data = self.get_data(response)
        for people in data['GridData']:
            loader = ItemLoader(CompaniesItem(),response)
            loader.add_value('first_name',people['FirstName'])
            loader.add_value('last_name',people['LastName'])
            loader.add_value('url',people['Url'])
            loader.add_value('title',people['AttorneyLevelTitle'])
            loader.add_value('email',people['BusinessEmail'] + '@' + people['BusinessEmailDomain'])
            loader.add_value('linkedin',people['LinkedInUrl'])
            loader.add_value('image','https://www.bakermckenzie.com' + people['PhotoUrl'])
            loader.add_value('firm_bio','https://www.bakermckenzie.com/en/aboutus')
            yield Request(
                loader._values['url'][0],
                callback = self.parse_people,
                meta = {
                    'loader': loader
                }
            )
    
    def parse_people(self,response):
        loader = response.meta['loader']
        loader.add_value('bio',response.xpath('string(//h3[contains(text(),"Biography")]/following-sibling::div)').get())
        loader.add_value('firm',response.css('div.association::text').get())
        loader.add_value('law_school',response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul/li[contains(text(),"Law") or contains(text(),"law")]/text()').get())
        
        try : 
            loader.add_value('law_school_graduation_year',findall(r'\d+',loader._values['law_school'][0]))
        except KeyError :
            self.logger.info('no law school graduation year available')

        loader.add_value('undergraduate_school',response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul/li[contains(text(),"Univ") or contains(text(),"univ")]/text()').get())
        
        try :
            loader.add_value('undergraduate_school_graduation_year',findall(r'\d+',loader._values['undergraduate_school'][0]))
        except KeyError :
            self.logger.info('no undergraduate_school_graduation_year available')
        
        loader.add_value('office',response.css('li.office a::text').get())
        yield loader.load_item()

    def get_data(self,response):
        script = response.xpath('//script[contains(text(),"initialJsonData")]/text()').get().replace('\\','')
        return chompjs.parse_js_object(script, json_params={'strict': False})