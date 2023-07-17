import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
import chompjs 
from scrapy.selector import Selector 


class SkaddenSpider(scrapy.Spider):
    name = 'burnslev'
    allowed_domains = ['burnslev.com']
    start_urls = ['https://www.burnslev.com/professionals/#/?view=All']

    # def __init__(self):
    #     self.not_names = ['Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
    #         + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]




    def parse(self, response):
        data = response.xpath('//script[contains(text(),"bio_data")]/text()').get()
        data_object = chompjs.parse_js_object(data)
        items = list(data_object.values())
        for item in items :
            loader = ItemLoader(CompaniesItem(),response)
            loader.add_value('url',response.urljoin(Selector(text=item['image']).xpath('//a/@href').get()))
            loader.add_value('first_name',item['first_name'])
            loader.add_value('last_name',item['last_name'])
            loader.add_value('firm',self.name)
            loader.add_value('title',item['job_title'])
            loader.add_value('email',Selector(text=item['email']).xpath('//a/@href').get().replace('mailto:',''))
            loader.add_value('image',response.urljoin(Selector(text=item['image']).xpath('//img/@src').get()))
            loader.add_value('firm_bio','https://www.burnslev.com/about-us/')
            try:
                loader.add_value('office',item['offices'][0])
            except IndexError :
                pass
            yield loader.load_item()



    def get_total_pages(self,response):
        pass 


    def get_law_school(self,educations_list):
        year = education = ''
        for edu in educations_list : 
            if 'law' in edu.lower() : 
                education = edu
                try :
                    year = findall('\d\d\d\d',education)[0]
                except IndexError : 
                    pass
                return education,year


    def get_undergraduate_school(self,educations_list):
        year = education = ''
        for edu in educations_list : 
            if not 'law' in edu.lower() : 
                education = edu
                try : 
                    year = findall('\d\d\d\d',education)[0]
                except IndexError : 
                    pass
                return education,year


                