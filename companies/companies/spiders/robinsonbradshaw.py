import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class SkaddenSpider(scrapy.Spider):
    name = 'robinsonbradshaw'
    allowed_domains = ['robinsonbradshaw.com']
    start_urls = ['https://www.robinsonbradshaw.com/professionals.html?do_item_search=1']

    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']




    def parse(self, response):
        people_divs = response.xpath('//p/following-sibling::div[@class="results_list"]/div')
        people_items = [
            ('https://www.robinsonbradshaw.com/'+div.css('span.title a::attr(href)').get(),div.css('span.position::text').get()) 
            for div in people_divs]
        for item in people_items :
            yield Request(
                item[0],
                callback =self.parse_individual,
                meta={
                    'title':item[1]
                }
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
        loader.add_value('title',response.meta['title'])
        try:
            loader.add_value('email',response.xpath('//a[contains(text(),"Email")]/@href').get().replace('mailto:',''))
        except AttributeError:
            pass
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::p')]
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
        loader.add_value('image',response.urljoin(response.css('img#bioPhoto::attr(src)').get()))
        loader.add_xpath('bio','string(//h1[contains(text(),"Profile")]/following-sibling::div[1])')
        loader.add_value('firm_bio','https://www.robinsonbradshaw.com/firm.html')
        loader.add_css('office','div#bioOfficeList a::text')
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


                