import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from companies.items import CompaniesItem
from re import findall


class DaypitneySpider(scrapy.Spider):
    name = 'daypitney'
    allowed_domains = ['daypitney.com']
    start_urls = ['https://www.daypitney.com/webapi/ProfessionalsApi/Search/?pageNum=0&pageSize=1000&startswith=']


    def parse(self, response):
        people_urls = [response.urljoin(individual['Url']) for individual in response.json()['data']['list']]
        for url in people_urls : 
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//h1/following-sibling::div/text()')
        loader.add_css('email','a.email::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('(//div[contains(text(),"Education")])[2]/following-sibling::div//div[@class="item"]')]
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
        loader.add_value('image',response.urljoin(response.css('div.bg-img-cover img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[contains(text(),"Overview")]/following-sibling::div)')
        loader.add_value('firm_bio','https://www.daypitney.com/about/general-content')
        loader.add_css('office','div.location a::text') # not just single value
        yield loader.load_item()


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