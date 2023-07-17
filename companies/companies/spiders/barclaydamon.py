import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class BarclaydamonSpider(scrapy.Spider):
    name = 'barclaydamon'
    allowed_domains = ['barclaydamon.com']
    start_urls = ['http://barclaydamon.com/']

    def __init__(self):
        self.listing_template = 'https://www.barclaydamon.com/ajax/BioSearch.aspx?page={}'


    def start_requests(self):
        yield Request(
            self.listing_template.format(1),
            method='POST',
            meta={
                'page':1
            }
        )


    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('a.bioCard__name::attr(href)').getall()]
        if not people_urls :
            return 
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )

        page = response.meta['page'] + 1
        yield Request(
                self.listing_template.format(page),
                method= 'POST',
                dont_filter = True,
                callback=self.parse_individual,
                meta={
                    'page':page
                }
        )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        loader.add_xpath('first_name','//h1/text()')
        loader.add_xpath('last_name','//h1/span/text()')
        loader.add_value('firm',self.name)
        loader.add_css('title','h3.hero__subtitle-heading::text')
        loader.add_css('email','div.bioInfo__email a::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul[1]/li')]
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
        loader.add_css('image','img.hero__image::attr(src)')
        loader.add_xpath('bio','string(//h3[contains(text(),"Biography")]/following-sibling::div[1])')
        loader.add_value('firm_bio','https://www.barclaydamon.com/Find-Us')
        loader.add_css('office','div.bioInfo__location a::text')
        yield loader.load_item()


    def get_total_pages(self,response):
        return int(response.xpath('//div[@class="searchPager"]/a[last()]/text()').get())        


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