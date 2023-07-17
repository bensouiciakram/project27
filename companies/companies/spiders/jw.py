import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem



class JwSpider(scrapy.Spider):
    name = 'jw'
    allowed_domains = ['jw.com']
    start_urls = ['http://jw.com/']

    def __init__(self):
        self.listing_template = 'https://www.jw.com/people/page/{}/'


    def start_requests(self):
        yield Request(
            self.listing_template.format(1),
        )

    def parse(self, response):
        total_pages = self.get_total(response)
        for page in range(1,total_pages + 1):
            yield Request(
                self.listing_template.format(page),
                callback = self.parse_individuals,
                dont_filter = True
            )

    def parse_individuals(self,response):
        people_urls = response.css('div.people-name a::attr(href)').getall()
        for url in people_urls : 
            yield Request(
                url,
                self.parse_individual ,
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.bio-affiliate-type::text')
        loader.add_xpath('email','//div[@class="bio-content hidden visible-print"]/text()')
        educations_list = response.xpath('//h2[contains(text(),"Education")]/following-sibling::p/text()').getall()
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
            loader.add_value('image',self.get_image(response))
        except TypeError :
            loader.add_value('image','no image')
        loader.add_value('bio',' '.join([p.xpath('string(.)').get() for p in response.xpath('//h2[contains(text(),"Biography")]/following-sibling::p')]))
        loader.add_value('firm_bio','https://www.jw.com/meet-jw/who-we-are/')
        loader.add_xpath('office','//div[@class="bio-affiliate-location"]/text()')
        yield loader.load_item()


    def get_total(self,response):
        return int(response.xpath('string(//div[@class="pagination"]//li[last()]/preceding-sibling::li[1])').get())


    def get_image(self,response):
        image_text = response.xpath('//style[@type="text/css" and contains(text(),"background-image")]/text()').get()
        regex = "url\('([\S]+)'\)"
        return findall(regex,image_text)[0]


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