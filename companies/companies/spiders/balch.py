import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
import chompjs 


class BalchSpider(scrapy.Spider):
    name = 'balch'
    allowed_domains = ['balch.com']
    start_urls = ['http://balch.com/']

    def __init__(self):
        self.listing_template = 'https://www.balch.com/people/?letter={}&skip={}'
        self.not_names = ['J.P.','Jr.','V','III','M.','II','J.','W.','R.','AICP','G.','IV','W.F.','D.','S.','R.','W.','C.','Dr.','F.','A.','P.']


    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch.upper(),0),
                callback= self.parse_individuals,
                meta={
                    'page':0,
                    'ch':ch
                }
            )


    def parse_individuals(self,response):
        text = response.xpath('//script[@type="text/javascript" and contains(text(),"initialJsonData")]/text()').get().replace('\r\n','').replace('\\','')
        people_urls =[response.urljoin(url) for url in findall('"Url":"(/people/\S+?)"',text)]
        page = response.meta['page'] + 1 
        if page > 3 :
            return 
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )
        ch = response.meta['ch']
        yield Request(
            self.listing_template.format(ch,20*page),
            callback = self.parse_individuals ,
            meta= {
                'page':page,
                'ch':ch
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
        loader.add_css('title','span.level::text')
        loader.add_xpath('email','//a[contains(@href,"@balch.com")]/text()')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[contains(text(),"Education")]/following-sibling::div//li')]
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
        loader.add_value('image',response.urljoin(response.css('div.hero-image::attr(style)').re('url\((\S+)\)')[0].replace("'",'')))
        loader.add_xpath('bio','string(//section[@id="about"])')
        loader.add_value('firm_bio','https://www.balch.com/about/about-us')
        loader.add_css('office','a.profile-card-location::text')
        yield loader.load_item()


    def get_data(self,response):
        return chompjs.parse_js_object(response.xpath('//script[@type="text/javascript" and contains(text(),"initialJsonData")]/text()').get().replace('\r\n','').replace('\\',''),json_params={'strict':False})


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