import scrapy
from scrapy import Request
import re 
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.shell import inspect_response


class SkaddenSpider(scrapy.Spider):
    name = 'wyattfirm'
    #allowed_domains = ['wyattfirm.com']
    start_urls = []

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]


    def start_requests(self):
        yield Request(
            'https://wyattfirm.com/wp-admin/admin-ajax.php?value=&term=keywords&values=&action=rrmw_team_search',
            dont_filter=True
        )


    def parse(self, response):
        regex = '"https:[\s\S]+?"'
        people_urls = {url.replace('\\','').replace('"','') for url in findall(regex,response.text) if 'team' in url }
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
        loader.add_xpath('title','//h1/following-sibling::h2/text()')
        loader.add_css('email','div.email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"EDUCATION")]/following-sibling::p')]
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
        loader.add_css('image','div.desktop-head img::attr(src)')
        loader.add_xpath('bio','string(//div[contains(@class,"overview-content")])')
        loader.add_value('firm_bio','https://wyattfirm.com/about/')
        loader.add_css('office','div.top-location a::text')
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


                