from scrapy import FormRequest, Request, Spider

from tcmba.items import ProcessItem


class ProcessesSpider(Spider):
    name = "processos"
    allowed_domains = ["www.tcm.ba.gov.br/"]
    start_urls = [
        "https://www.tcm.ba.gov.br/consulta/jurisprudencia/consulta-ementario-juridico/#todos/"  # noqa
    ]
    handle_httpstatus_list = [302]

    def parse(self, response):
        descriptions = response.css("table#tabela tr td a span::text").extract()
        file_urls = response.css("table#tabela tr td a::attr(href)").extract()
        process_numbers = response.css(
            "table#tabela tr td:nth-child(1)::text"
        ).extract()

        assert len(descriptions) == len(file_urls) == len(process_numbers)

        for process_number, description, file_url in zip(
            process_numbers, descriptions, file_urls
        ):
            item = ProcessItem(
                process_number=process_number,
                description=description,
                file_url=file_url,
            )
            yield Request(
                "https://www.tcm.ba.gov.br/consulta-processual/",
                dont_filter=True,
                callback=self.parse_process,
                meta={"item": item},
            )

    def parse_process(self, response):
        yield FormRequest.from_response(
            response,
            method="POST",
            dont_filter=True,
            formxpath='.//form[@name="formProtocolo"]',
            formdata={
                "proc": response.meta["item"]["process_number"],
                "consulta": "ok",
                "B1": "+Consultar+",
            },
            callback=self.parse_details,
            meta={"item": response.meta["item"]},
        )

    def get_history(self, table):
        units = table.css("td:nth-child(1)")
        entry_dates = table.css("td:nth-child(2)")
        statuses = table.css("td:nth-child(3)")
        notes = table.css("td:nth-child(4)")

        history = []

        for unit, entry_date, status, note in zip(units, entry_dates, statuses, notes):
            unit_str = unit.css("::text").get()
            entry_date_str = entry_date.css("::text").get()
            status_str = status.css("::text").get()
            note_str = note.css("::text").get()

            history.append(
                {
                    "unity": unit_str.strip() if unit_str else "",
                    "entry_date": entry_date_str.strip() if entry_date_str else "",
                    "situation": status_str.strip() if status_str else "",
                    "notes": note_str.strip() if note_str else "",
                }
            )
        return history

    def get_field(self, response, label):
        field_str = response.xpath(
            f"//label[contains(text(),'{label}')]/following-sibling::span/text()"
        ).get()
        if field_str:
            return field_str.strip()
        return ""

    def parse_details(self, response):
        item = response.meta["item"]
        item["process_at"] = response.css("div.subtitle span::text").get()
        item["entry_at"] = self.get_field(response, "Data de Entrada:")
        item["nature"] = self.get_field(response, "Natureza:")
        item["complement"] = self.get_field(response, "Complemento:")
        item["city"] = self.get_field(response, "Município:")
        item["author"] = self.get_field(response, "Interessado/Autor:")
        item["received"] = self.get_field(response, "Recebido(S/N):")
        item["last_update_at"] = self.get_field(response, "Data:")
        item["unit"] = self.get_field(response, "Unidade:")
        item["history"] = self.get_history(response.css("table#tabelaResultado"))
        item["number_of_origin_document"] = self.get_field(
            response, "Nº Doc.de Origem:"
        )
        item["entrance"] = self.get_field(response, "Meio:")
        item["document_date"] = self.get_field(response, "Data do Documento:")
        item["attachments"] = self.get_field(response, "Anexos:")
        item["notes"] = self.get_field(response, "Observações:")
        item["place_of_origin"] = self.get_field(response, "Local de Origem:")
        yield item
