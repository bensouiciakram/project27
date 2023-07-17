import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.shell import inspect_response


class SkaddenSpider(scrapy.Spider):
    name = 'vonbriesen'
    allowed_domains = ['vonbriesen.com']
    start_urls = ['https://www.vonbriesen.com/professional-profiles']


    def __init__(self):
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']


    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('td.content-table__row--name a::attr(href)').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback =self.parse_individual
            )



    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        if any(name == fullname_list[0] for name in self.not_names):
            loader.add_value('first_name', fullname_list[1])
        else :
            loader.add_value('first_name', fullname_list[0])
        if any(name == fullname_list[-1] for name in self.not_names):
            loader.add_value('last_name', fullname_list[-2])
        else :
            loader.add_value('last_name', fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.bio-title::text')
        loader.add_value('email',self.get_email(response))
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('(//p[contains(text(),"Education")]/following-sibling::ul)[1]/li')]
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
        loader.add_value('image',response.urljoin(response.css('img.bio-image::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="bio-content"])')
        loader.add_value('firm_bio','https://www.vonbriesen.com/the-firm')
        loader.add_css('office','span.list-item__text::text')
        yield loader.load_item()


    def get_total(self,response):
        pass 


    def get_email(self,response):
        return '{}@{}.{}'.format(response.css('a.cryptedmail::attr(data-name)').get(),response.css('a.cryptedmail::attr(data-domain)').get(),response.css('a.cryptedmail::attr(data-tld)').get())

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