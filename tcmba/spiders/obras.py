from datetime import date, datetime

from scrapy import Request, Spider
from scrapy.selector import Selector

from tcmba.items import ConstructionItem
from tcmba.spiders.helpers import format_year


def get_span_value_for_label(response, label):
    value = (
        response.css(".form-group")
        .xpath(f".//span[preceding-sibling::label[contains(., '{label}')]]/text()")
        .get()
    )
    return value if value else ""


def get_table_rows(response, search_text):
    table = response.xpath(
        f".//table[thead[tr[./th[contains(text(), '{search_text}')]]]]"
    )
    rows = table.css("tbody tr")
    return rows


class ConstructionsSpider(Spider):
    name = "obras"
    url = "https://www.tcm.ba.gov.br/portal-da-cidadania/obras/"
    current_year = date.today().year

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "ano_inicial"):
            try:
                int(self.ano_inicial)
                self.ano_inicial = int(format_year(self.ano_inicial))
                if self.ano_inicial > self.current_year:
                    raise Exception("O ano informado não pode ser no futuro.")
            except ValueError:
                raise Exception("Você precisa informar um ano válido.")
        else:
            self.ano_inicial = date.today().year

        if hasattr(self, "cidade"):
            try:
                self.cidade = int(self.cidade)
            except ValueError:
                raise Exception(
                    "Você precisa um código de cidade válido. O código IBGE deve ser numérico."
                )
        else:
            # Código IBGE de Feira de Santana
            self.cidade = 2910800

        if hasattr(self, "entidade"):
            try:
                self.entidade = int(self.entidade)
            except ValueError:
                raise Exception("Você precisa um código de entidade válido.")
        else:
            # 129 é o código de entidade da Prefeitura Mun. de Feira de Santana
            self.entidade = 129

    def start_requests(self):
        year = self.ano_inicial
        while year <= self.current_year:
            url = f"{self.url}?municipio={self.cidade}&ano={year}&entidade={self.entidade}&pesquisar=Pesquisar"
            year += 1
            yield Request(url, self.parse)

    def parse(self, response):
        rows = response.css("table#tabelaResultado tbody tr")

        for row in rows:
            detail_url = (
                row.css(".btn-acao::attr(onclick)")
                .re_first(r"location.=\s*(.*)")
                .replace("'", "")
            )

            popover_content_text = row.css("a.btn-popover::attr(data-content)").get()
            company_content = Selector(text=popover_content_text)

            item = ConstructionItem(
                construction_number=row.xpath(".//td[1]/text()").get(),
                description=row.xpath(".//td[2]/text()").get(),
                situation=row.xpath(".//td[3]/text()").get(),
                type=row.xpath(".//td[4]/text()").get(),
                work_or_service_value=row.xpath(".//td[5]/text()").get(),
                paid_value=row.xpath(".//td[6]/text()").get(),
                retained_value=row.xpath(".//td[7]/text()").get(),
                executing_company={
                    "cnpj": company_content.css("td:nth-child(1)::text").get(),
                    "name": company_content.css("td:nth-child(2)::text").get(),
                },
                crawled_at=datetime.now(),
            )

            yield Request(
                detail_url, callback=self.parse_details, cb_kwargs={"item": item}
            )

    def parse_details(self, response, item):
        item["process_number"] = get_span_value_for_label(response, "Processo")
        item["homologation"] = get_span_value_for_label(response, "Homologação")
        item["competence"] = get_span_value_for_label(response, "Competência")
        item["bid_value"] = get_span_value_for_label(response, "Valor Licitação")
        item["bidding_procedure"] = get_span_value_for_label(
            response, "Proced. Licitatório"
        )
        item["form"] = get_span_value_for_label(response, "Forma")
        item["operation"] = item["form"] = get_span_value_for_label(
            response, "Operação"
        )
        item["source"] = item["form"] = get_span_value_for_label(response, "Fonte")

        item["additives"] = self.get_additives(response)
        item["payments"] = self.get_payments(response)
        yield item

    def get_additives(self, response):
        additives = []
        rows = get_table_rows(response, "Aditivo")
        for row in rows:
            additives.append(
                {
                    "number": row.xpath(".//td[1]/text()").get(),
                    "entry_date": row.xpath(".//td[2]/text()").get(),
                    "start_date": row.xpath(".//td[3]/text()").get(),
                    "term_calendar_days": row.xpath(".//td[4]/text()").get(),
                    "value": row.xpath(".//td[5]/text()").get(),
                    "quarter": row.xpath(".//td[6]/text()").get(),
                }
            )

        return additives

    def get_payments(self, response):
        payments = []
        rows = get_table_rows(response, "Valor Pago")
        for row in rows:
            payments.append(
                {
                    "date": row.xpath(".//td[1]/text()").get(),
                    "effort_number": row.xpath(".//td[2]/text()").get(),
                    "process_number": row.xpath(".//td[3]/text()").get(),
                    "paid_value": row.xpath(".//td[4]/text()").get(),
                    "quarter": row.xpath(".//td[5]/text()").get(),
                }
            )
        return payments
