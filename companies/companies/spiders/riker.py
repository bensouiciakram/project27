import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SkaddenSpider(scrapy.Spider):
    name = 'riker'
    allowed_domains = ['riker.com']
    start_urls = ['http://riker.com/attorneys']

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.'] \
            + [ch.upper() + '.' for ch in 'abcdefghijklmnopqrstuvwxyz' ]




    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.xpath('//select[@id="people"]//option[@value]/@value').getall()]
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
        loader.add_xpath('title','//h2/text()')
        try: 
            loader.add_value('email',response.css('li#attorney-heading-contact-email a::attr(href)').get().replace('mailto:',''))
        except AttributeError :
            pass
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h4[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_value('image',response.urljoin(response.css('img.attorney-portrait::attr(src)').get()))
        loader.add_css('bio','main.attorney-body p::text')
        loader.add_value('firm_bio','http://riker.com/about-us')
        loader.add_xpath('office','//h4[contains(text(),"Bar Admissions")]/following-sibling::ul/li[1]/text()')
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


                