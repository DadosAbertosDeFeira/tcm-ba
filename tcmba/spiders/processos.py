import scrapy


class ProcessesSpider(scrapy.Spider):
    name = "processos"
    allowed_domains = ["www.tcm.ba.gov.br/"]
    start_urls = [
        "https://www.tcm.ba.gov.br/consulta/jurisprudencia/consulta-ementario-juridico/#todos/"
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
            data = {
                "numero_processo": process_number,
                "descricao": description,
                "arquivo": file_url,
            }
            yield scrapy.Request(
                "https://www.tcm.ba.gov.br/consulta-processual/",
                dont_filter=True,
                callback=self.parse_process,
                meta={"data": data},
            )

    def parse_process(self, response):
        yield scrapy.FormRequest.from_response(
            response,
            method="POST",
            dont_filter=True,
            formxpath='.//form[@name="formProtocolo"]',
            formdata={
                "proc": response.meta["data"]["numero_processo"],
                "consulta": "ok",
                "B1": "+Consultar+",
            },
            callback=self.parse_details,
            meta={"data": response.meta["data"]},
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
                    "unidade": unit_str.strip() if unit_str else "",
                    "data_de_entrada": entry_date_str.strip() if entry_date_str else "",
                    "situacao": status_str.strip() if status_str else "",
                    "observacao": note_str.strip() if note_str else "",
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
        process_data = response.meta["data"]
        process_data["processado_em"] = response.css("div.subtitle span::text").get()
        process_data["data_de_entrada"] = self.get_field(response, "Data de Entrada:")
        process_data["natureza"] = self.get_field(response, "Natureza:")
        process_data["complemento"] = self.get_field(response, "Complemento:")
        process_data["municipio"] = self.get_field(response, "Município:")
        process_data["interessado_autor"] = self.get_field(
            response, "Interessado/Autor:"
        )
        process_data["recebido"] = self.get_field(response, "Recebido(S/N):")
        process_data["data_da_ultima_atualizacao"] = self.get_field(response, "Data:")
        process_data["unidade"] = self.get_field(response, "Unidade:")
        process_data["movimentacao"] = self.get_history(
            response.css("table#tabelaResultado")
        )
        process_data["numero_documento_de_origem"] = self.get_field(
            response, "Nº Doc.de Origem:"
        )
        process_data["meio"] = self.get_field(response, "Meio:")
        process_data["data_do_documento"] = self.get_field(
            response, "Data do Documento:"
        )
        process_data["anexos"] = self.get_field(response, "Anexos:")
        process_data["observacoes"] = self.get_field(response, "Observações:")
        process_data["local_de_origem"] = self.get_field(response, "Local de Origem:")
        yield process_data
