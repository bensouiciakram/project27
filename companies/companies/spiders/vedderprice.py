import scrapy
from scrapy import Request
from playwright.sync_api import sync_playwright
from math import ceil
from re import findall
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class VedderpriceSpider(scrapy.Spider):
    name = 'vedderprice'
    allowed_domains = ['vedderprice.com']
    start_urls = ['https://www.vedderprice.com/sitecore/api/ssc/webapi/search/1/professionals?pageSize=500&pageNum=0&sortBy=0&sortOrder=0&loadAllByPageSize=false']

    def start_requests(self):
        yield Request(
            self.start_urls[0],
            headers={
                "accept": "application/json, text/plain, */*",
            },
            callback= self.parse_individuals

        )
    

    def parse_individuals(self,response):
        people_urls = [response.urljoin(item['Url']) for item in response.json()['data']['list']]
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )
            
    def parse_individual(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//div[@class="professionals-detail-tab__name"]/h1/text()').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','(//h1/following-sibling::p)[1]/text()')
        loader.add_css('email','span.email-disclaimer--js::text') 
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::ul/li')]
        try :
            law_school , year = self.get_law_school(educations_list)
            loader.add_value('law_school',law_school)
            loader.add_value('law_school_graduation_year',year)
        except TypeError : 
            pass 
        try: 
            undergraduate_school, year = self.get_undergraduate_school(educations_list)
            loader.add_value('undergraduate_school',undergraduate_school)
            loader.add_value('undergraduate_school_graduation_year',year)
        except TypeError : 
            pass
        loader.add_xpath('image','//meta[@property="og:image"]/@content')
        loader.add_xpath('bio','string(//div[@class="professionals-detail-tab__bio detail-tab__richtext-container"])')
        loader.add_value('firm_bio','https://www.vedderprice.com/about-us')
        loader.add_xpath('office','string(//a[@class="professionals-detail-tab__contact-link"])')
        yield loader.load_item()


    def get_total_page(self,page):
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