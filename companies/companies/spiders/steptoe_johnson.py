import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SteptoeJohnsonSpider(scrapy.Spider):
    name = 'steptoe_johnson'
    allowed_domains = ['steptoe-johnson.com']
    start_urls = ['https://www.steptoe-johnson.com/people']

    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('h4 a::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('(//h2)[1]/text()').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','(//div[@class="row"][2]//div[@class="field-item even"])[1]/text()')
        loader.add_xpath('email','//a[@data-toggle="modal"]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[contains(@class,"field-name-field-profile-education")]//div[text()]')]
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
        loader.add_xpath('image','(//img[@class="img-responsive"])[2]/@src')
        loader.add_xpath('bio','string(//h2[contains(text(),"Biography")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.steptoe-johnson.com/about-us')
        loader.add_xpath('office','string(//div[contains(text(),"Office")]/following-sibling::div)')
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
