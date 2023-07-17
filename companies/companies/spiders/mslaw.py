import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from math import ceil
import w3lib.html 
import traceback 
from scrapy.shell import inspect_response


class MslawSpider(scrapy.Spider):
    name = 'mslaw'
    allowed_domains = ['mslaw.com']
    start_urls = ['http://mslaw.com/']

    headers = {
        'Accept':'application/json, text/plain, */*',
        'X-Index':'miles_production'
    }

    def __init__(self):
        self.listing_template = 'https://api2.greatjakes.com/people?search[post_type]=person&from={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(0),
            headers=self.headers
        )


    def parse(self, response):
        total_pages = self.get_total_pages(response)
        for page in range(total_pages):
            yield Request(
                self.listing_template.format(30*page),
                headers=self.headers,
                callback=self.parse_individuals,
                dont_filter=True
            )


    def parse_individuals(self,response):
        individuals = response.json()['content']['hits']['person']['hits']
        for individual in individuals :
            loader = ItemLoader(CompaniesItem(),response)
            loader.add_value('url',response.url)
            loader.add_value('first_name',individual['_source']['first_name'])
            loader.add_value('last_name',individual['_source']['last_name'])
            loader.add_value('firm',self.name)
            loader.add_value('title',individual['_source']['position'][0]['term'])
            loader.add_value('email',individual['_source']['email'])
            try: 
                    educations_list = ['{} {}'.format(edu['school'][0]['term'],edu['year']) for edu in individual['_source']['education_fieldset']]
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
            except KeyError :
                    pass
            try: 
                loader.add_value('image',individual['_source']['headshot_photo']['url'])
            except KeyError :
                pass
            bio_first_part = individual['_source']['full_content']
            try :
                bio_second_part = individual['_source']['full_content_continued']
            except KeyError :
                bio_second_part = ''
            bio = bio_first_part + '\n' + bio_second_part 
            loader.add_value('bio',w3lib.html.remove_tags(bio))
            loader.add_value('firm_bio','https://www.mslaw.com/about-us')
            loader.add_value('office',individual['_source']['office_location'][0]['post_title'])
            yield loader.load_item()


    def get_total_pages(self,response):
        return ceil(response.json()['content']['hits']['person']['total']/30)


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