import scrapy
from scrapy.selector import Selector
from scrapy import Request
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from re import findall



class WeilSpider(scrapy.Spider):
    name = 'weil'
    allowed_domains = ['weil.com']
    start_urls = ['https://www.weil.com/WeilPeopleListing/Execute?pagenum=1&pagesize=2000']
    

    def parse(self, response):
        people_urls = []
        data = response.json()
        for ch in data['SearchGroups']:
            for individual in ch['SearchResultItemsAsHtml']:
                selector = Selector(text=individual)
                people_urls.append(self.extract_url(selector,response))

        for url in people_urls : 
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//div[@class="layout-a row"]//h1/text()').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.h3::text')
        loader.add_xpath('email','//a[contains(text(),"@weil.com")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h1[contains(text(),"Education")]/ancestor::header/following-sibling::ul//li')]
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
        loader.add_value('firm_bio','https://www.weil.com/about-weil')
        loader.add_xpath('bio','string(//section[@class="col-1"])')
        loader.add_css('office','span.h3 span::text')
        yield loader.load_item()


    def extract_url(self,selector,response):
        return response.urljoin(selector.css('h3 a::attr(href)').get())

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