import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from re import findall

class SquirepattonboggsSpider(scrapy.Spider):
    name = 'squirepattonboggs'
    allowed_domains = ['squirepattonboggs.com']
    start_urls = ['https://www.squirepattonboggs.com/api/professionals/search?letter=&pageSize=2000']

    def parse(self, response):
        people_urls = [response.urljoin(individual['url']) for individual in response.json()['data']['list']]
        for url in people_urls : 
            yield Request(
                url,
                callback = self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_xpath('title','//h1/following-sibling::h2/text()')
        loader.add_xpath('email','string(//a[@class="contact-email"])')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul[1]/li')]
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
        loader.add_value('image',response.urljoin(response.css('div.contact-details img::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="description-wrapper"])')
        loader.add_value('firm_bio','https://www.squirepattonboggs.com/en/about/overview')
        loader.add_css('office','div.office-name a::text') # don't use takefirst contains several office
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