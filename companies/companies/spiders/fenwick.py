import scrapy
from scrapy import Request
from playwright.sync_api import sync_playwright
from math import ceil
from re import findall
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class FenwickSpider(scrapy.Spider):
    name = 'fenwick'
    allowed_domains = ['fenwick.com']
    start_urls = ['http://fenwick.com/']

    listing_post_url = 'https://osxpwx1xyl-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.1.0)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.3.1)%3B%20JS%20Helper%20(3.1.1)&x-algolia-api-key=ed2cb03e2103c101b212c4f6810e8a12&x-algolia-application-id=OSXPWX1XYL'
    body_template = '{{"requests":[{{"indexName":"prod_main_alpha_sort","params":"tagFilters=%5B%22attorneys%22%2C%22en%22%5D&query=&highlightPreTag=__ais-highlight__&highlightPostTag=__%2Fais-highlight__&page={}&maxValuesPerFacet=999&facets=%5B%22relatedOffice%22%2C%22employeeType%22%2C%22alphaFacet%22%2C%22relatedIndustries%22%2C%22relatedPractices%22%2C%22education%22%5D"}}]}}'
    headers ={
        'content-type': 'application/x-www-form-urlencoded'
    }

    def start_requests(self):
        body = self.body_template.format(0)
        yield Request(
            url=self.listing_post_url,
            method='POST',
            dont_filter=True,
            headers=self.headers,
            body=body,
            callback= self.parse
        )

    
    def parse(self,response):
        total_pages = response.json()['results'][0]['nbPages']
        for page in range(total_pages):
            body = self.body_template.format(page)
            yield Request(
                url=self.listing_post_url,
                method='POST',
                dont_filter=True,
                headers=self.headers,
                body=body,
                callback= self.parse_individuals,
            )


    def parse_individuals(self,response):
        people_urls = [item['url'] for item in response.json()['results'][0]['hits']]
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual,
            )


    def parse_individual(self, response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h5[1]/text()')
        try:
            loader.add_value('email',response.xpath('//p[@class="side--attorney__cta"]/a/@href').get().replace('mailto:',''))        
        except AttributeError :
            loader.add_value('email','no email')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education & Admissions")]/following-sibling::p')]
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

        loader.add_css('image','aside img::attr(src)')
        loader.add_xpath('bio','string(//div[@class="content-block body-copy-block rich-text-typography body-copy-block-spacing"])')
        loader.add_value('firm_bio','https://www.fenwick.com/firm')
        loader.add_xpath('office','//div[@class="attorney-sidebar-info"]/h5[last()]/text()')
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