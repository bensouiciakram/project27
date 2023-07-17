import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class LowensteinSpider(scrapy.Spider):
    name = 'lowenstein'
    allowed_domains = ['lowenstein.com']
    start_urls = ['https://www.lowenstein.com/umbraco/Surface/PeopleDirectory/GetPeopleDirectoryResultsAll?pageId=1261&letter=&practice=&location=&position=&pageSize=500&lawSchool=&college=&undergraduate=&subTotal=8']


    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.xpath('//div[@class="item visible-xs visible-sm"]//h2/a/@href').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback= self.parse_individual
            )

    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//h1/text()').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_xpath('title','//div[@id="freeRole"]/p/text()')
        loader.add_css('email','span#email-attorney-mobile a::text')
        educations_list = set([edu.xpath('string(.)').get() for edu in response.xpath('//h2[contains(text(),"Education")]/following-sibling::ul/li/p')])
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
        loader.add_value('image',response.urljoin(response.css('div.headline img::attr(src)').get()))
        loader.add_value('bio',' '.join([p.xpath('string(.)').get() for p in response.xpath('//section[@class="experience"]/ancestor::div[1]/preceding-sibling::div[1]//p')]))
        loader.add_value('firm_bio','https://www.lowenstein.com/about-us')
        loader.add_xpath('office','//div[@id="Attorney-bio"]/div[1]/span/text()')
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