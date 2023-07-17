import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall


class GtlawSpider(scrapy.Spider):
    name = 'gtlaw'
    allowed_domains = ['gtlaw.com']
    start_urls = ['https://www.gtlaw.com/sitecore/api/ssc/webapi/search/1/search?searchType=Professionals&pageSize=1000&pageNum=2']

    def parse(self, response):
        data = response.json()['data']
        people_urls = [
            'https://www.gtlaw.com' + individual['Url'] for individual in data['list']
        ]
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().strip().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','span.main-title::text')
        loader.add_css('email','a.email span::text')
        educations_list = [edu.xpath('string(.)').get().strip() for edu in response.xpath('//div[contains(text(),"Education")]/following-sibling::ul/li')]
        try:
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
        loader.add_value('image',response.urljoin(response.css('div.image-container img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="main-content rich-text"])')
        loader.add_value('firm_bio','https://www.gtlaw.com/en/our-firm')
        loader.add_css('office','div.office-item a::text')
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