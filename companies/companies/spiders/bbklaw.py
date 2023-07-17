import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class BbklawSpider(scrapy.Spider):
    name = 'bbklaw'
    allowed_domains = ['bbklaw.com']
    start_urls = ['http://bbklaw.com/']


    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
    }

    body = '{"CurrentPage":1,"PageCount":500}'


    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']


    def start_requests(self):
        yield Request(
            'https://www.bbklaw.com/api/search/professionals',
            method='POST',
            headers= self.headers,
            body=self.body
        )

    def parse(self, response):
        people_urls =[response.urljoin(item['URL']) for item in response.json()['Items']]
        for url in people_urls :
            yield Request(
                url ,
                callback =self.parse_individual
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
        loader.add_xpath('title','//h1/following-sibling::p/text()')
        loader.add_xpath('email','//h4[contains(text(),"@bbklaw.com")]/text()')
        educations_list = []
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
        loader.add_value('image',response.urljoin(response.css('div.bio--pic--thumbnail img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@id="profile"])')
        loader.add_value('firm_bio','https://www.bbklaw.com/about')
        loader.add_xpath('office','(//div[contains(@class,"dropdown-info")]/p)[1]/text()')
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