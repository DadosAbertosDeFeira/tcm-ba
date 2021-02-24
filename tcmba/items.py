from scrapy import Item, Field


class DocumentItem(Item):
    category = Field()
    filename = Field()
    inserted_by = Field()
    inserted_at = Field()
    unit = Field()
