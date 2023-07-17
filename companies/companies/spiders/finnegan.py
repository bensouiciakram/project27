import scrapy
from scrapy.selector import Selector 
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem   

class FinneganSpider(scrapy.Spider):
    name = 'finnegan'
    allowed_domains = ['finnegan.com']
    start_urls = ['https://www.finnegan.com/_site/search?s=1000&f=0&v=attorney&html=true']

    def parse(self, response):
        selector = Selector(text=response.json()['rendered_view'])
        people_urls = [response.urljoin(url) for url in selector.css('dt a::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback= self.parse_individual
            )

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().strip().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::p/text()')
        loader.add_xpath('email','//a[contains(@data-href,"mailto:")]/text()')
        educations_list = [edu.xpath('string(.)').get().strip() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::dl')]
        try :
            law_school , year = self.get_law_school(educations_list)
            loader.add_value('law_school',law_school)
            loader.add_value('law_school_graduation_year',year)
        except TypeError : 
            pass 
        try : 
            undergraduate_school, year = self.get_undergraduate_school(educations_list)
            loader.add_value('undergraduate_school',undergraduate_school)
            loader.add_value('undergraduate_school_graduation_year',year)
        except TypeError :
            pass
        loader.add_css('image','img.detail-hero__image::attr(src)')
        loader.add_xpath('bio','string(//div[@id="profile"])')
        loader.add_value('firm_bio','https://www.finnegan.com/en/firm/index.html')
        try :
            loader.add_value('office',response.xpath('//div[contains(@class,"detail-hero__details")]/div/ul/li[last()]/text()').get().strip().split()[0].replace(',',''))
        except AttributeError :
            pass
        yield loader.load_item()


    def get_total(self,response):
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