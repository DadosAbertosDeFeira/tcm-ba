from scrapy import Field, Item


class DocumentItem(Item):
    category = Field()
    filename = Field()
    inserted_by = Field()
    inserted_at = Field()
    unit = Field()


class ProcessItem(Item):
    process_number = Field()
    description = Field()
    process_number = Field()
    file_url = Field()
    entry_at = Field()
    process_at = Field()
    entry_at = Field()
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
