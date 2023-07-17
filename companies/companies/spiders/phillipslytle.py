import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class PhillipslytleSpider(scrapy.Spider):
    name = 'phillipslytle'
    allowed_domains = ['phillipslytle.com']
    start_urls = ['https://phillipslytle.com/our-people/team/']

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']


    def parse(self, response):
        people_urls = response.css('div.person-thumb>div>a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::p/b/text()')
        loader.add_xpath('email','//h1/following-sibling::p/a/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::div//li')]
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
        loader.add_css('image','img.person-photo::attr(src)')
        loader.add_value('bio',' '.join([sel.xpath('string(.)').get() for sel in response.xpath('//p[@class="introcopy"]') + response.xpath('//p[@class="introcopy"]/following-sibling::p')]))
        loader.add_value('firm_bio','https://phillipslytle.com/about-us/')
        loader.add_xpath('office','//h1/following-sibling::p/br/following-sibling::text()')
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