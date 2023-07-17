import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from playwright.sync_api import sync_playwright
import pandas as pd 

class BuchalterSpider(scrapy.Spider):
    name = 'buchalter'
    allowed_domains = ['buchalter.com']
    start_urls = ['https://www.buchalter.com/attorneys/']


    def parse(self, response):
        people_urls = response.css('h2.name a::attr(href)').getall()
        for url in people_urls :
            yield Request(
                url,
                callback= self.parse_individual
            )
     

    def parse_individual(self,response):


        with sync_playwright() as p :
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(response.url)
            email = page.query_selector('//a[@itemprop="email"]').inner_text()

        yield {
            'bar':'',
            'bio':response.xpath('string(//aside[@id="aside-overview"])').get(),
            'email':email,
            'firm':self.name,
            'firm_bio':'https://www.buchalter.com/about-buchalter/',
            'first_name':response.xpath('//span[@itemprop="givenName"]/text()').get().split()[0],
            'image':response.css('img#attorney-photo::attr(src)').get(),
            'last_name': response.xpath('//span[@itemprop="familyName"]/text()').get(),
            'law_school':'',
            'law_school_graduation_year':'',
            'linkedin':'',
            'office':response.xpath('//span[contains(text(),"Offices:")]/following-sibling::a/text()').get(),
            'title': response.xpath('//h2[@itemprop="jobTitle"]/text()').get(),
            'undergraduate_school':'',
            'undergraduate_school_graduation_year':'',
            'url':response.url,
            'education':response.xpath('string(//aside[@id="aside-education"])').get()
        }


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

