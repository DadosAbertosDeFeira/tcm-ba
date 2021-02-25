import logging

from parsel import Selector
from scrapy import FormRequest, Request, Spider

from tcmba.items import DocumentItem

from .helpers import (format_city, format_month_and_year, format_period,
                      format_year)

logger = logging.getLogger(__name__)


class ConsultaPublicaSpider(Spider):
    name = "consulta_publica"
    start_urls = ["https://e.tcm.ba.gov.br/epp/ConsultaPublica/listView.seam"]

    def __init__(self, *args, **kwargs):
        """Inicializa o spider com os argumentos prontos para serem utilizados."""
        super(ConsultaPublicaSpider, self).__init__(*args, **kwargs)

        if hasattr(self, "cidade"):
            self.cidade = format_city(self.cidade)
        else:
            raise Exception("Você precisa informar uma cidade.")

        if hasattr(self, "periodicidade"):
            if self.periodicidade.lower() in ("anual", "mensal"):

                if hasattr(self, "competencia"):
                    if "anual" in self.periodicidade:
                        try:
                            int(self.competencia)
                        except:
                            raise Exception("Você precisa informar um ano válido.")
                        else:
                            self.competencia = format_year(self.competencia)
                    elif "mensal" in self.periodicidade:
                        try:
                            # FIXME checar formato com regex
                            self.competencia
                        except:
                            raise Exception(
                                "Você precisa informar o mês no formato MM/YYYY."
                            )
                        else:
                            self.competencia = format_month_and_year(self.competencia)

                self.periodicidade = format_period(self.periodicidade)
            else:
                raise Exception(
                    "Periodicidade inválida (precisa ser `anual` ou `mensal`)."
                )
        else:
            raise Exception(
                "Você precisa informar uma periodicidade (precisa ser `anual` ou `mensal`)."
            )

        logger.info(
            f"Argumentos: `{self.cidade}` `{self.periodicidade}` `{self.competencia}`"
        )

    def parse(self, response):
        print(self.cidade)

        form_id = "consultaPublicaTabPanel:consultaPublicaPCSearchForm"

        payload = {
            f"{form_id}:PeriodicidadePC_input": self.periodicidade,
            f"{form_id}:competenciaPC_input": self.competencia,
            f"{form_id}:municipio_input": self.city,
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": f"{form_id}:searchButton",
            "javax.faces.partial.event": "click",
            "javax.faces.partial.execute": f"{form_id}:searchButton @component",  # noqa
            "javax.faces.partial.render": "@component",
            "org.richfaces.ajax.component": f"{form_id}:searchButton",
            "{form_id}:searchButton": f"{form_id}:searchButton",
            "rfExt": "null",
            "AJAX:EVENTS_COUNT": "1",
        }

        yield FormRequest.from_response(
            response=response,
            formid=form_id,
            formdata=payload,
            callback=self.get_search_results,
        )

    def get_search_results(self, response):
        selector = self.get_selector(response)

        result_rows = selector.xpath(
            "//tbody[@id='consultaPublicaTabPanel:consultaPublicaDataTable:tb']//tr"  # noqa
        )
        view_state = selector.xpath(
            "//*[@id='javax.faces.ViewState']/text()"
        ).get()  # noqa

        # TODO: Parsear todos os resultados
        for table_row in [result_rows[0]]:
            columns = table_row.xpath("./td")

            form_id = self.get_form_id(columns[0])

            payload = {
                form_id: form_id,
                "javax.faces.ViewState": view_state,
                "javax.faces.source": f"{form_id}:selecionarPrestacao",
                "javax.faces.partial.event": "click",
                "javax.faces.partial.execute": f"{form_id}:selecionarPrestacao @component",  # noqa
                "javax.faces.partial.render": "@component",
                "org.richfaces.ajax.component": f"{form_id}:selecionarPrestacao",  # noqa
                f"{form_id}:selecionarPrestacao": f"{form_id}:selecionarPrestacao",  # noqa
                "rfExt": "null",
                "AJAX:EVENTS_COUNT": "1",
                "javax.faces.partial.ajax": "true",
            }

            yield FormRequest(
                url="https://e.tcm.ba.gov.br/epp/ConsultaPublica/listView.seam",  # noqa
                formdata=payload,
                callback=self.get_detailed_results,
            )

    def get_detailed_results(self, response):
        selector = self.get_selector(response)

        result_rows = selector.xpath(
            "//tbody[@id='consultaPublicaTabPanel:tabelaDocumentos_data']//tr"
        )
        view_state = selector.xpath(
            "//*[@id='javax.faces.ViewState']/text()"
        ).get()  # noqa
        unit = selector.xpath(
            "//span[@id='consultaPublicaTabPanel:unidadeJurisdicionadaDecoration:unidadeJurisdicionada']/text()"  # noqa
        ).get()

        payloads = []

        for row in result_rows:
            columns = row.xpath("./td")
            texts = [
                text.strip()
                for text in columns.xpath(".//text()").extract() or []
                if text.strip()
            ]

            item = DocumentItem(
                category=texts[0],
                filename=texts[1],
                inserted_by=texts[2],
                inserted_at=texts[3],
                unit=unit,
            )

            form_id = self.get_form_id(columns[0])

            payload = {
                form_id: form_id,
                "javax.faces.ViewState": view_state,
                "javax.faces.source": f"{form_id}:downloadDocBinario",
                "javax.faces.partial.event": "click",
                "javax.faces.partial.execute": f"{form_id}:downloadDocBinario @component",  # noqa
                "javax.faces.partial.render": "@component",
                "org.richfaces.ajax.component": f"{form_id}:downloadDocBinario",  # noqa
                f"{form_id}:downloadDocBinario": f"{form_id}:downloadDocBinario",  # noqa
                "rfExt": "null",
                "AJAX:EVENTS_COUNT": "1",
                "javax.faces.partial.ajax": "true",
            }

            payloads.append(
                dict(
                    url="https://e.tcm.ba.gov.br/epp/ConsultaPublica/listView.seam",  # noqa
                    formdata=payload,
                    callback=self.prepare_file_request,
                    meta={"item": item, "payloads": payloads},
                )
            )

        payload = payloads.pop(0)

        yield FormRequest(**payload)

    def prepare_file_request(self, response):
        yield Request(
            url="https://e.tcm.ba.gov.br/epp/PdfReadOnly/downloadDocumento.seam",  # noqa
            callback=self.save_file,
            meta=response.meta,
            dont_filter=True,
        )

    def save_file(self, response):

        item = response.meta["item"]
        payloads = response.meta["payloads"]
        payload = payloads.pop(0) if payloads else None

        # TODO: Mover para Middlewares?
        with open(
            f"{self.settings['FILES_STORE']}/{item['filename']}", "wb"
        ) as fp:  # noqa
            fp.write(response.body)

        for value in (item, payload):
            if isinstance(value, DocumentItem):
                yield value
            else:
                if value:
                    yield FormRequest(**value)

    def get_selector(self, response):
        source_code = (
            response.xpath("//partial-response//changes")
            .get()
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
        selector = Selector(text=source_code)
        return selector

    def get_form_id(self, selector):
        return selector.xpath("./form/@id").get()
