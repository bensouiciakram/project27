import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class LitchfieldcavoSpider(scrapy.Spider):
    name = 'litchfieldcavo'
    allowed_domains = ['litchfieldcavo.com']
    start_urls = ['https://www.litchfieldcavo.com/our-attorneys/']


    def start_requests(self):
        for url in self.start_urls :
            yield Request(
                'https://www.litchfieldcavo.com/our-attorneys/',
                method= 'POST',
                headers={ "content-type": "application/x-www-form-urlencoded",},
                body = 'whole_name_search=&keyword_search=&office_search=&covid_search=&display_form=1&attorney_submit=Submit'
                )


    def parse(self, response):
        people_urls = response.css('div.attorney-name>a::attr(href)').getall()
        for url in people_urls : 
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h2.position::text')
        loader.add_value('email',''.join(response.css('a.email::text').getall()))
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul//li')]
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
        try: 
            loader.add_value('image',response.css('div.image img::attr(src)').getall()[-1])
        except IndexError :
            loader.add_value('image','no image')
        loader.add_value('bio',' '.join([p.xpath('string(.)').get() for p in response.css('div#panel1 p')]))
        loader.add_value('firm_bio','https://www.litchfieldcavo.com/about-us/')
        loader.add_xpath('office','//h2[@class="position"]/following-sibling::div//span/text()')
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