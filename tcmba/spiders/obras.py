from datetime import date, datetime

from scrapy import Request, Spider
from scrapy.selector import Selector

from tcmba.items import ConstructionItem
from tcmba.spiders.helpers import format_year


class ConstructionsSpider(Spider):
    name = "obras"
    url = "https://www.tcm.ba.gov.br/portal-da-cidadania/obras/?municipio=2910800"
    current_year = date.today().year

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "ano_inicial"):
            try:
                int(self.ano_inicial)
                self.ano_inicial = int(format_year(self.ano_inicial))
            except ValueError:
                raise Exception("Você precisa informar um ano válido.")
        else:
            self.ano_inicial = date.today().year

    def start_requests(self):
        year = self.ano_inicial
        while year <= self.current_year:
            # 129 é o código de entidade da Prefeitura Mun. de Feira de Santana
            url = f"{self.url}&ano={year}&entidade=129&pesquisar=Pesquisar"
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
                    "cnpj": company_content.css('td:nth-child(1)::text').get(),
                    "name": company_content.css('td:nth-child(2)::text').get(),
                },
                crawled_at=datetime.now(),
            )

            request = Request(detail_url, callback=self.parse_details)
            request.cb_kwargs["item"] = item
            yield request

    def parse_details(self, response, item):
        values = response.css(".form-group").xpath(".//span//text()").getall()

        item["process_number"] = values[1]
        item["homologation"] = values[2]
        item["competence"] = values[3]
        item["bid_value"] = values[4]
        item["bidding_procedure"] = values[5]
        item["form"] = values[6]
        item["operation"] = values[7]
        item["source"] = values[8]

        item["additives"] = self.get_additives(response)
        item["payments"] = self.get_payments(response)
        yield item

    def get_additives(self, response):
        additives = []
        table = response.xpath(".//table[thead[tr[./th[contains(text(), 'Aditivo')]]]]")
        rows = table.css("tbody tr")
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
        table = response.xpath(
            ".//table[thead[tr[./th[contains(text(), 'Valor Pago')]]]]"
        )
        rows = table.css("tbody tr")
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
