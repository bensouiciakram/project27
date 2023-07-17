import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
import chompjs 
from scrapy import Selector 


class SkaddenSpider(scrapy.Spider):
    name = 'bodmanlaw'
    allowed_domains = ['bodmanlaw.com']
    start_urls = ['https://www.bodmanlaw.com/attorneys/#/?view=All&page=1']

    def __init__(self):
        self.not_names = ['E.','J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']




    def parse(self, response):
        data = response.xpath('//script[@type="text/javascript" and contains(text(),"search_json")]').get()
        data_object=chompjs.parse_js_object(data)['sorted_children']
        people_urls = ['https://www.bodmanlaw.com'+Selector(text=item['formatted_name']).xpath('//a/@href').get() for item in data_object]
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
        try:
            loader.add_value('email',response.css('li.email a::attr(href)').get().replace('mailto:',''))
        except AttributeError :
            pass
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h6[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_css('image','div#bioImage::attr(style)')
        loader.add_xpath('bio','string(//div[@id="overview"])')
        loader.add_value('firm_bio','https://www.bodmanlaw.com/about-Bodman/')
        loader.add_xpath('office','//h1/following-sibling::h2/a/text()')
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


                