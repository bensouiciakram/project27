# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst

def strip_field(field_list):
    return [
        field.strip() for field in field_list
    ]

class CompaniesItem(scrapy.Item):
    first_name = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    last_name = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    firm = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    title = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    email = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    linkedin = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )
    law_school_graduation_year = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )
    law_school = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )
    undergraduate_school_graduation_year = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )
    undergraduate_school = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )
    image = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    bio = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    firm_bio = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )
    url = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    office = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
    bar = scrapy.Field(
        input_processor = strip_field,
        output_processor = TakeFirst()
    )#
