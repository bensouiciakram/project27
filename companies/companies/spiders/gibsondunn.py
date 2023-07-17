import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall


class GibsondunnSpider(scrapy.Spider):
    name = 'gibsondunn'
    allowed_domains = ['gibsondunn.com']
    start_urls = ['https://www.gibsondunn.com/?search=lawyer&s=&school=']


    def __init__(self):
        self.listing_template = 'https://www.gibsondunn.com/?paged1={}&search=lawyer&type=lawyer&s&school'

    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(1,total_pages + 1):
            yield Request(
                self.listing_template.format(page),
                callback=self.parse_individuals,
                dont_filter = True
            )

    
    def parse_individuals(self,response):
        people_urls = set(response.xpath('//div[contains(@class,"search-result-mobile-section")]//a[1]/@href').getall())
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual,
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list =response.css('h2#full_name::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','h2#designation::text')
        loader.add_css('email','a.email-custom-btn::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"EDUCATION")]/following-sibling::p')]
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
        loader.add_css('image','div.profile_photo img::attr(src)')
        loader.add_value('firm_bio','https://www.gibsondunn.com/about-gibson-dunn/')
        loader.add_xpath('bio','string(//section[@id="biography-section"])')
        loader.add_css('office','a.main-office-btn::text')
        yield loader.load_item()





    def get_total_pages(self,response):
        return int(response.xpath('//a[@class="page-numbers"][last()]/text()').get())

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