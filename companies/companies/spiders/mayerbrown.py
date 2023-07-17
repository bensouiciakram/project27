import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from re import findall

class MayerbrownSpider(scrapy.Spider):
    name = 'mayerbrown'
    allowed_domains = ['mayerbrown.com']
    start_urls = ['https://www.mayerbrown.com/sitecore/api/ssc/webapi/people/1/search?page=1&pageSize=2000']

    def parse(self, response):
        data = response.json()
        people_urls = [response.urljoin(individual['url']) for individual in data['results']]
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
        loader.add_value('firm',self.name)
        loader.add_css('title','div.hero__subtitle::text')
        loader.add_xpath('email','//a[@class="link link__underlined contact-card__email"]/span/text()')
        educations_list = response.xpath('//h3[contains(text(),"Education")]/following-sibling::div/p/text()').getall()
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
        loader.add_value('image',response.urljoin(response.css('div.professional img::attr(src)').get()))
        loader.add_value('firm_bio','https://www.mayerbrown.com/en/about-us/about?tab=Overview')
        loader.add_css('office','a.contact-card__office::text')
        loader.add_xpath('bio','string(//div[@class="block__row richtext"])')
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