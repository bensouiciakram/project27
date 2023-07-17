import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class WickersmithSpider(scrapy.Spider):
    name = 'wickersmith'
    allowed_domains = ['wickersmith.com']
    start_urls = ['http://wickersmith.com/']

    def __init__(self):
        self.listing_template = 'https://www.wickersmith.com/professionals/page/{}/'
        self.not_names = ['J.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']


    def start_requests(self):
        yield Request(
            self.listing_template.format(1)
        )

    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(1,total_pages+1):
            yield Request(
                self.listing_template.format(page),
                callback= self.parse_individuals,
                dont_filter=True
            )

    def parse_individuals(self,response):
        people_urls = response.css('h3 a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('div.bio-details h1::text').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::h4/text()')
        loader.add_value('email',response.xpath('string(//h4/following-sibling::p[1])').get().replace(' Email: ',''))
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//strong[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_css('image','div.bio-pic img::attr(src)')
        loader.add_value('bio',' '.join(response.xpath('//h3[contains(text(),"Biography")]/following-sibling::p/text()').getall()))
        loader.add_value('firm_bio','https://www.wickersmith.com/profile/firm-overview/')
        loader.add_xpath('office','//p[contains(text(),"Offices")]/a/text()')
        yield loader.load_item()


    def get_total_pages(self,response):
        return int(response.xpath('(//a[@class="page-numbers"])[last()]/text()').get())


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