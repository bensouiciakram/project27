import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from re import findall



class BclplawSpider(scrapy.Spider):
    name = 'bclplaw'
    allowed_domains = ['bclplaw.com']
    start_urls = ['http://bclplaw.com/']

    def __init__(self):
        self.listing_template = 'https://www.bclplaw.com/_site/v1/search?ctx=&s={}&type=attorney'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0),
            meta={
                'page':0
            }
        )


    def parse(self, response):
        data = response.json()
        page = response.meta['page']
        if data['hits']:
            page += 1
            yield Request(
                self.listing_template.format(page),
                meta={
                    'page':page
                }
            )
        
        people_urls = [response.urljoin(individual['url']) for individual in response.json()['hits']]
        for url in people_urls :
            yield Request(
                url ,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader =ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('(//h1)[1]/text()').get().strip().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','(//span[@class="attorney-header__position  bclp-orange"])[1]/text()')
        loader.add_xpath('email','(//span[@class="hide-for-print attorney-header__email--address"])[1]/text()')
        educations_list =   [edu.xpath('string(.)').get() for edu in response.xpath('(//h2[descendant::span[contains(text(),"Education")]])[2]/following-sibling::div//p')]
        try :
            law_school , year = self.get_law_school(educations_list)
            loader.add_value('law_school',law_school)
            loader.add_value('law_school_graduation_year',year)
        except TypeError : 
            pass 
        try: 
            undergraduate_school, year = self.get_undergraduate_school(educations_list)
            loader.add_value('undergraduate_school',undergraduate_school)
            loader.add_value('undergraduate_school_graduation_year',year)
        except TypeError : 
            pass
        loader.add_value('image',self.get_image(response))
        loader.add_value('firm_bio','https://www.bclplaw.com/en-US/about/history.html')
        loader.add_xpath('bio','string((//div[@class="rte contains-pdf-breaks"])[1])')
        loader.add_css('office','a.attorney-header__office-item::text')
        yield loader.load_item()






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



    def get_image(self,response):
        string = response.css('div.attorney-image style::text').get()
        regex = 'url\((\S+)\)'
        return findall(regex,string)[0]
