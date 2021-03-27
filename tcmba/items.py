from scrapy import Field, Item


class BaseItem(Item):
    crawled_at = Field()


class DocumentItem(BaseItem):
    category = Field()
    filename = Field()
    original_filename = Field()
    filepath = Field()
    inserted_by = Field()
    inserted_at = Field()
    unit = Field()
    month = Field()
    year = Field()
    period = Field()


class ProcessItem(BaseItem):
    process_number = Field()
    description = Field()
    file_url = Field()
    entry_at = Field()
    process_at = Field()
    nature = Field()
    complement = Field()
    city = Field()
    author = Field()
    received = Field()
    last_update_at = Field()
    unit = Field()
    history = Field()
    number_of_origin_document = Field()
    entrance = Field()
    document_date = Field()
    attachments = Field()
    notes = Field()
    place_of_origin = Field()
