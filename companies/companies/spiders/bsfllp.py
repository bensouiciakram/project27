import scrapy
from scrapy import Request
from re import findall 
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy.selector import Selector


class BsfllpSpider(scrapy.Spider):
    name = 'bsfllp'
    allowed_domains = ['bsfllp.com']
    start_urls = ['https://www.bsfllp.com/_site/search?l=&html&v=filtered_attorney']

    def parse(self,response):
        selector = Selector(text = response.json()['rendered_view'])
        people_urls = [response.urljoin(url) for url in selector.css('a.search__result-lawyer-name-link::attr(href)').getall()]
        for url in people_urls : 
            yield Request(
                url,
                callback= self.parse_individual
            )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        loader.add_value('url',response.url)
        fullname_list = response.css('h1::text').get().split()
        loader.add_value('first_name', fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',self.name)
        loader.add_css('title','div.page-header__title p::text')
        loader.add_value('email',response.xpath('(//a[contains(text(),"Email")])[1]/@data-href').get().replace('mailto:',''))
        educations_list = [edu.xpath('string(.)').get() for edu in response.xpath('//span[contains(text(),"Education")]/ancestor::h3/following-sibling::div//li')]
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
        loader.add_css('image','img.page-header__cover-image::attr(src)')
        loader.add_xpath('bio','string(//span[contains(text(),"Profile")]/ancestor::h2/following-sibling::div)')
        loader.add_value('firm_bio','https://www.bsfllp.com/about-us/overview.html')
        loader.add_css('office','dt a::text')
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


    def get_total(self,response):
        return ceil(response.json()['totals']['ALL']/100)