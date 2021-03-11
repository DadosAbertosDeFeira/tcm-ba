from scrapy import Field, Item


class DocumentItem(Item):
    category = Field()
    filename = Field()
    inserted_by = Field()
    inserted_at = Field()
    unit = Field()
