import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class MvalawSpider(scrapy.Spider):
    name = 'mvalaw'
    allowed_domains = ['mvalaw.com']
    start_urls = ['https://www.mvalaw.com/people?results#form-search-results']


    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.xpath('//div[@class="nametitle"]/div[@class="title"]/a/@href').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        loader.add_xpath('first_name','//span[@itemprop="givenName"]/text()')
        loader.add_xpath('last_name','//span[@itemprop="familyName"]/text()')
        loader.add_value('firm',self.name)
        loader.add_css('title','div#bioTitle::text')
        loader.add_css('email','li#bioEmail a::text')
        educations_list = response.xpath('//div[@id="bio_education"]//p/text()').getall()
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
        loader.add_value('image',response.urljoin(response.xpath('//div[@id="bannerImage"]/img[1]/@src').get()))
        loader.add_xpath('bio','string(//h2[contains(text(),"Overview")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.mvalaw.com/about-our-firm')
        # office not found
        #loader.add_('office',)
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