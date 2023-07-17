import scrapy
from scrapy import Request,FormRequest
from scrapy.loader import  ItemLoader
from companies.items import CompaniesItem
from re import findall

class LewisbrisboisComSpider(scrapy.Spider):
    name = 'lewisbrisbois'
    allowed_domains = ['lewisbrisbois.com']
    start_urls = ['https://lewisbrisbois.com/attorneys/search-results/eyJyZXN1bHRfcGFnZSI6ImF0dG9ybmV5c1wvc2VhcmNoLXJlc3VsdHMiLCJjb2xsZWN0aW9uIjoiMSJ9']


    def __init__(self):
        self.listing_template = 'https://lewisbrisbois.com/attorneys/search-results/eyJyZXN1bHRfcGFnZSI6ImF0dG9ybmV5c1wvc2VhcmNoLXJlc3VsdHMiLCJjb2xsZWN0aW9uIjoiMSJ9/P{}'


    def start_requests(self):
        yield Request(
            self.start_urls[0],
            meta= {
                'page':0
            }
        )

    def parse(self, response):
        if  'No attorneys found.' in response.text : 
            return
        else :
            page = response.meta['page'] + 50
            yield FormRequest(
                self.listing_template.format(page),
                meta= {
                    'page':page
                }
            )

        people_urls = [response.urljoin(url) for url in response.xpath('//ul/li/a/@href').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback = self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h2::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','p.sub-heading::text')
        loader.add_xpath('email','//img[@alt="email icon"]/following-sibling::a/text()')
        educations_list =[edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::h6')]
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
        loader.add_xpath('image','//div[@id="attorney-hero-info"]/preceding-sibling::img/@src')
        loader.add_value('firm_bio','https://lewisbrisbois.com/about/firm-overview')
        loader.add_value('bio',' '.join([sel.xpath('string(.)').get() for sel in response.xpath('//div[@id="biography"]/p')]))
        loader.add_css('office','li.location strong::text')
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