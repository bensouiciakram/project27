import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall
import requests



class ReedsmithSpider(scrapy.Spider):
    name = 'reedsmith'
    allowed_domains = ['reedsmith.com']
    start_urls = ['http://reedsmith.com/']

    headers = {
        'authority': 'www.reedsmith.com',
        'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json;charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
        'sec-ch-ua-platform': '"Linux"',
        'origin': 'https://www.reedsmith.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.reedsmith.com/en/professionals',
        'accept-language': 'en-US,en;q=0.9',
        }
    data = '{{"Letter":"{}","Name":"","Keyword":"","Take":500,"Skip":0,"AttachedFilters":[]}}'

    def __init__(self):
        self.listing_template = 'https://www.reedsmith.com/en/professionals?page=1&letter={}'

    
    def start_requests(self):
        for ch in 'abcdefghijklmnopqrstuvwxyz':
            yield Request(
                self.listing_template.format(ch.upper()),
                meta={
                    'ch':ch
                }
            )

    
    def parse(self,response):
        data = self.data.format(response.meta['ch'])
        res = requests.post('https://www.reedsmith.com/api/professionals/search', headers=self.headers, data=data)
        data = res.json()
        people_urls = [
            response.urljoin(individual['Url']) for individual in data['Results'] 
        ]

        for url in people_urls : 
            yield Request(
                url,
                callback = self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1.professional-header-name::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.professional-header-position::text')
        # email can't be obtained unless you made a demand 
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//div[@id="education"]//li')]
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
        loader.add_value('image',response.urljoin(response.css('figure img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="read-more-intro rte"])')
        loader.add_value('firm_bio','https://www.reedsmith.com/en/about-us')
        loader.add_css('office','a.professional-header-office::text')
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
