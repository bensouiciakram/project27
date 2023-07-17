import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SkaddenSpider(scrapy.Spider):
    name = 'kbrlaw'
    allowed_domains = ['kbrlaw.com']
    start_urls = ['http://www.kbrlaw.com/home/professionals']

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]




    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.xpath('//a[contains(@href,"/professional/")]/@href').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback =self.parse_individual
            )



    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('div.banner-prodetail-inf>span::text').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-2] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-3].replace(',',''))
        else :
            loader.add_value('last_name', fullname_list[-2].replace(',',''))
        loader.add_value('firm',self.name)
        loader.add_value('title',response.css('div.banner-prodetail-inf>span::text').get().split(',')[-1])
        loader.add_xpath('email','//div[@class="banner-prodetail-inf"]/span[2]/text()[2]')
        base_xpath = '//span[contains(text(),"Education")]/ancestor::strong'
        xpath1 = '/following-sibling::text()'
        xpath2 = '/ancestor::p/following-sibling::p[1]/text()'
        educations_list = response.xpath(base_xpath + xpath1 +'|'+base_xpath + xpath2).getall()
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
        loader.add_value('image',response.urljoin(response.css('div.banner-prodetail-img img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="infopro-detail"])')
        loader.add_value('firm_bio','http://www.kbrlaw.com/home/pages/intro')
        loader.add_xpath('office','//div[@class="banner-prodetail-inf"]/span[2]/text()[1]')
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


                