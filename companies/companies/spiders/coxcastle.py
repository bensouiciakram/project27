import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright 
from scrapy.selector import Selector 


class SkaddenSpider(scrapy.Spider):
    name = 'coxcastle'
    allowed_domains = ['coxcastle.com']
    start_urls = ['https://www.coxcastle.com/people-landing?nameStart=All']

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]




    def parse(self, response):
        people_divs = response.css('table.people-table>tbody')
        for div in people_divs :
            loader = ItemLoader(CompaniesItem(),div)
            loader.add_value('url',response.urljoin(div.xpath('.//td[1]/a/@href').get()))
            fullname_list = div.xpath('string(.//td[1])').get().split()
            if any(name == fullname_list[0] for name in self.not_names):
                loader.add_value('first_name', fullname_list[1].replace(',',''))
            else :
                loader.add_value('first_name', fullname_list[0].replace(',',''))
            if any(name == fullname_list[-1] for name in self.not_names):
                loader.add_value('last_name', fullname_list[-2])
            else :
                loader.add_value('last_name', fullname_list[-1])
            loader.add_value('firm',self.name)
            loader.add_xpath('title','string(.//td[2])')
            try :
                loader.add_value('email',div.xpath('.//td[5]/ul/li[1]/a/@href').get().replace('mailto:',''))
            except AttributeError :
                pass
            # educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[contains(text(),"Education")]/ancestor::div[1]/following-sibling::div//li')]
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
            #loader.add_value('image','https://www.coxcastle.com'+response.css('figure img::attr(src)').get())
            #loader.add_xpath('bio','string(//div[@id="MainContent"])')
            loader.add_value('firm_bio','https://www.coxcastle.com/our-firm')
            loader.add_xpath('office','string(.//td[3])')
            yield loader.load_item()



    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('string((//h1)[last()])').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.sub-title::text')
        loader.add_css('email','dd.email-wrap>a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[contains(text(),"Education")]/ancestor::div[1]/following-sibling::div//li')]
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
        loader.add_value('image','https://www.coxcastle.com'+response.css('figure img::attr(src)').get())
        loader.add_xpath('bio','string(//div[@id="MainContent"])')
        loader.add_value('firm_bio','https://www.coxcastle.com/our-firm')
        loader.add_xpath('office','//address/span[last()]/text()')
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


                