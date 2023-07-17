import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem


class WinsteadSpider(scrapy.Spider):
    name = 'winstead'
    allowed_domains = ['winstead.com']
    start_urls = ['https://www.winstead.com/People/Search?search=']


    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('div.atty_name a::attr(href)').getall()]
        for url in people_urls :
            yield Request(
                url,
                callback=self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.xpath('//table[@class="details_wrapper"]/@data-full-name').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        regex = 'bioTitle : ([\s\S]+?),'
        loader.add_value('title',findall(regex,response.xpath('//script[contains(text(),"bioTitle")]/text()').get())[0].replace("'",''))
        loader.add_css('email','a.atty_email::text')
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//h3[contains(text(),"Education")]/following-sibling::ul/li')]
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
        loader.add_value('image',response.urljoin(findall("headerImageSrc  : ([\s\S]+),",response.xpath('//script[contains(text(),"bioTitle")]/text()').get())[0].replace("'",'')))
        loader.add_xpath('bio','string(//div[@id="atty_tab_content"])')
        loader.add_value('firm_bio','https://www.winstead.com/About-Winstead')
        loader.add_css('office','a.office_title_link::text')
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