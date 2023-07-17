import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall 


class SidleySpider(scrapy.Spider):
    name = 'sidley'
    allowed_domains = ['sidley.com']
    start_urls = ['http://sidley.com/']

    def __init__(self):
        self.listing_template = 'https://www.sidley.com/en/global/people/?letter={}&skip={}'

    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz' :
            yield Request(
                self.listing_template.format(ch.upper(),0),
                meta = {
                    'ch':ch
                }
            )

    
    def parse(self,response):
        skip = self.get_skip(response)
        ch = response.meta['ch']
        yield Request(
            self.listing_template.format(ch,skip),
            callback=self.parse_individuals
        )


    def parse_individuals(self,response):
        for url in self.get_people_urls(response):
            yield Request(
                url,
                callback=self.parse_individual
            )
    

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.level::text')
        loader.add_xpath('email','//div[@class="people-hero-body"]/a/text()')
        educations_list = [sel.xpath('string(.)').get() for sel in response.xpath('//h3[contains(text(),"Education")]/following-sibling::div//li')]
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
        loader.add_value('image',response.urljoin(response.css('img.people-hero-pic::attr(src)').get()))
        loader.add_xpath('bio','string((//div[@class="rich-text-content"])[1])')
        loader.add_value('firm_bio','https://www.sidley.com/en/ourstory/aboutsidley')
        loader.add_xpath('office','//li[@itemprop="location"]/a/text()')
        yield loader.load_item()

    def get_skip(self,response):
        script = response.xpath('//script[@type="text/javascript" and contains(text(),"initialJsonData")]/text()').get().replace('\\','')
        regex ='"ResultCount":(\d+)'
        total = int(findall(regex,script)[0])
        return (total//20)*20

    def get_people_urls(self,response):
        script = response.xpath('//script[@type="text/javascript" and contains(text(),"initialJsonData")]/text()').get().replace('\\','')
        regex = '"Url":"(/en/people[\S]+?)"'
        return ['https://www.sidley.com'+ url for url in set(findall(regex,script))]


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
    