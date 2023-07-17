import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SkaddenSpider(scrapy.Spider):
    name = 'taftlaw'
    allowed_domains = ['taftlaw.com']
    start_urls = ['https://www.taftlaw.com/api/query/people?perpage=1000&page=1&peopletype=all&getall=true']

    def __init__(self):
        self.not_names = ['Jr','Ph.D.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]




    def parse(self, response):
        people_urls = ['https://www.taftlaw.com'+item['url'] for item in response.json()['results'] ]
        for url in people_urls :
            yield Request(
                url,
                callback =self.parse_individual
            )



    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('string(//h1)').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.PositionOffices__position_0::text')
        loader.add_xpath('email','//span[@class="ContactInfoContent__letter_0"]/following-sibling::a/text()')
        # educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('')]
        # try :
        #     law_school , year = self.get_law_school(educations_list)
        #     loader.add_value('law_school',law_school)
        #     loader.add_value('law_school_graduation_year',year)
        # except TypeError : 
        #     pass 
        # try : 
        #     undergraduate_school, year = self.get_undergraduate_school(educations_list)
        #     loader.add_value('undergraduate_school',undergraduate_school)
        #     loader.add_value('undergraduate_school_graduation_year',year)
        # except TypeError :
        #     pass
        loader.add_xpath('image','//div[contains(@class,"print-image")]/@style',re='url\((\S+)\)')
        loader.add_xpath('bio','string(//h2[contains(text(),"Summary")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.taftlaw.com/about/about-us')
        loader.add_css('office','a.PositionOffices__office_0::text')
        yield loader.load_item()


    def get_total_pages(self,response):
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


                