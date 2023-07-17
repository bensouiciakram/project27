import scrapy
from scrapy.loader import ItemLoader 
from companies.items import CompaniesItem
from scrapy import Request
from re import findall 


class MorganlewisSpider(scrapy.Spider):
    name = 'morganlewis'
    allowed_domains = ['morganlewis.com']
    start_urls = [
        'https://www.morganlewis.com/api/custom/peoplesearch/search?keyword=&category=bb82d24a9d7a45bd938533994c4e775a&sortBy=lastname&pageNum=1&numberPerPage=3000&numberPerSection=5&enforceLanguage=&languageToEnforce=&school=&position=&location=&court=&judge='
        ]

    custom_settings = {
        'HTTPCACHE_ENABLED' : True
    }

    def parse(self, response):
        people_urls = [response.urljoin(url) for url in response.css('div.c-content-team__card a.c-content_team__link::attr(href)').getall()]
        for url in people_urls : 
           yield Request(
               url,
               callback= self.parse_individual,
           )


    def parse_individual(self,response):
        loader = ItemLoader(CompaniesItem(),response)
        fullname_list = response.css('span[itemprop=name]::text').get().split()
        loader.add_value('first_name',fullname_list[0])
        loader.add_value('last_name',fullname_list[-1])
        loader.add_value('firm',".morgan lewis")
        loader.add_css('title','div.person-heading-container h2::text')
        loader.add_css('email','a[itemprop=email]::text')
        loader.add_value('image',response.urljoin(response.css('img[itemprop=image]::attr(src)').get()))
        loader.add_xpath('bio','string(//div[@class="heading-brief"])')
        loader.add_value('firm_bio','https://www.morganlewis.com/our-firm/about-us')
        loader.add_value('url',response.url)
        loader.add_css('office','a[itemprop=location]::text')
        loader.add_css('bar','p.off-add::text')
        try :
            law = self.get_law_education(response)
            if not law :
                try :
                    loader.add_value('law_school',law[0])
                except :
                    pass
                try :
                    loader.add_value('law_school_graduation_year',law[1])
                except :
                    pass
        except IndexError:
           pass

        try : 
            undergraduate = self.get_graduation_education(response)
            if not undergraduate :
                try:
                    loader.add_value('undergraduate_school',undergraduate[0])
                except :
                    pass
                try :
                    loader.add_value('undergraduate_school_graduation_year',undergraduate[1])
                except :
                    pass
        except IndexError :
            pass
        yield loader.load_item()



    def get_law_education(self,response):
        strip_edu = [edu.strip() for edu in response.xpath('//div[@class="block print-education"]//li/text()').getall()]
        educations = [edu for edu in strip_edu if edu]

        education = year =  ''

        for education in educations : 
            if 'law' in education.lower() :
                try :
                    year = findall('\d\d\d\d',education)[0]
                except IndexError : 
                    self.logger.info('no year available')
                return education,year
        return None

    def get_graduation_education(self,response):
        strip_edu = [edu.strip() for edu in response.xpath('//div[@class="block print-education"]//li/text()').getall()]
        educations = [edu for edu in strip_edu if edu]

        education = year =  ''

        for education in educations : 
            if 'col' in education.lower() or 'univ' in education.lower() and not 'law' in education.lower():
                try :
                    year = findall('\d\d\d\d',education)[0]
                except IndexError : 
                    self.logger.info('no year available')
                if not year : 
                    year = ''
                return education,year
        return None