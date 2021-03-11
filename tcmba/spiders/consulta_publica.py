import logging
import re
from datetime import date, timedelta
from pathlib import Path
from re import search, sub
from uuid import uuid4

from parsel import Selector
from scrapy import FormRequest, Request, Spider
from os.path import sep as path_separator

from tcmba.items import DocumentItem

from .helpers import format_city, format_month_and_year, format_period, format_year

logger = logging.getLogger(__name__)


class ConsultaPublicaSpider(Spider):
    name = "consulta_publica"

    SEARCH_ENDPOINT = "https://e.tcm.ba.gov.br/epp/ConsultaPublica/listView.seam"
    DOWNLOAD_ENDPOINT = "https://e.tcm.ba.gov.br/epp/PdfReadOnly/downloadDocumento.seam"

    start_urls = [SEARCH_ENDPOINT]

    def __init__(self, *args, **kwargs):
        """Inicializa o spider com os argumentos prontos para serem utilizados."""
        super(ConsultaPublicaSpider, self).__init__(*args, **kwargs)

        if hasattr(self, "cidade"):
            self.cidade = format_city(self.cidade)
        else:
            self.cidade = format_city("Feira de Santana")

        if hasattr(self, "unidade") is False:
            self.unidade = ""

        if hasattr(self, "periodicidade"):
            self.periodicidade = format_period(self.periodicidade)
            if self.periodicidade not in ("Anual", "Mensal"):
                raise Exception(
                    "Você precisa informar uma periodicidade válida (anual ou mensal)."
                )
        else:
            self.periodicidade = "Mensal"

        if "anual" in self.periodicidade.lower():
            if hasattr(self, "competencia"):
                try:
                    int(self.competencia)
                except ValueError:
                    raise Exception("Você precisa informar um ano válido.")
            else:
                self.competencia = date.today().year
            self.competencia = format_year(self.competencia)
        elif "mensal" in self.periodicidade.lower():
            if hasattr(self, "competencia") is False:
                fourthy_days_ago = date.today() - timedelta(days=40)
                self.competencia = date.strftime(fourthy_days_ago, "%m/%Y")
            else:
                try:
                    match = re.search(r"\d{2}\/\d{4}", self.competencia)
                    self.competencia = match.group()
                except AttributeError:
                    raise Exception("Você precisa informar o mês no formato MM/YYYY.")
            self.competencia = format_month_and_year(self.competencia)

        logger.info(
            f"Argumentos: `{self.cidade}` "
            f"`{self.periodicidade}` "
            f"`{self.competencia}` "
            f"`{self.unidade}`"
        )

    def parse(self, response):
        form_id = "consultaPublicaTabPanel:consultaPublicaPCSearchForm"

        payload = {
            f"{form_id}:PeriodicidadePC_input": self.periodicidade,
            f"{form_id}:competenciaPC_input": self.competencia,
            f"{form_id}:municipio_input": self.cidade,
            f"{form_id}:unidadeJurisdicionada_input": self.unidade,
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

        pages = []
        total_pages = selector.xpath("//*[@class='rf-insl-mx']/text()").get() or 0
        if total_pages and total_pages.isnumeric():
            pages = list(range(2, int(total_pages) + 1))

        unit_payloads = []
        pagination_payloads = []

        for table_row in result_rows:
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

            unit_payloads.append(
                dict(
                    url=self.SEARCH_ENDPOINT,
                    formdata=payload,
                    callback=self.get_detailed_results,
                    meta={
                        "unit_payloads": unit_payloads,
                        "pagination_payloads": pagination_payloads,
                    },
                    dont_filter=True,
                )
            )

        if pages:
            form_id = selector.xpath(
                "//*[@class='rf-insl-mx']/ancestor::form/@id"
            ).get()
            pagination_id = selector.xpath(
                "//*[@class='rf-insl-mx']/ancestor::span/@id"
            ).get()

            for page in pages:
                payload = {
                    form_id: form_id,
                    pagination_id: str(page),
                    "javax.faces.ViewState": view_state,
                    "javax.faces.source": pagination_id,
                    "javax.faces.partial.event": "mousedown",
                    "javax.faces.partial.execute": f"{pagination_id} @component",
                    "javax.faces.partial.render": "@component",
                    "javax.faces.behavior.event": "change",
                    "org.richfaces.ajax.component": pagination_id,
                    "rfExt": "null",
                    "AJAX:EVENTS_COUNT": "1",
                    "javax.faces.partial.ajax": "true",
                }

                pagination_payloads.append(payload)

        unit_payload = unit_payloads.pop(0)

        yield FormRequest(**unit_payload)

    def paginate_units(self, response):
        pagination_payloads = response.meta["pagination_payloads"]
        unit_payloads = response.meta["unit_payloads"]

        selector = self.get_selector(response)

        result_rows = selector.xpath(
            "//tbody[@id='consultaPublicaTabPanel:consultaPublicaDataTable:tb']//tr"  # noqa
        )

        view_state = selector.xpath(
            "//*[@id='javax.faces.ViewState']/text()"
        ).get()  # noqa

        for table_row in result_rows:
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

            unit_payloads.append(
                dict(
                    url=self.SEARCH_ENDPOINT,
                    formdata=payload,
                    callback=self.get_detailed_results,
                    meta={
                        "unit_payloads": unit_payloads,
                        "pagination_payloads": pagination_payloads,
                    },
                    dont_filter=True,
                )
            )

        if pagination_payloads:
            payload = pagination_payloads.pop(0)

            yield FormRequest(
                url=self.SEARCH_ENDPOINT,
                formdata=payload,
                meta={
                    "pagination_payloads": pagination_payloads,
                    "unit_payloads": unit_payloads,
                },
                callback=self.paginate_units,
            )
        else:
            unit_payload = unit_payloads.pop(0)
            yield FormRequest(**unit_payload)

    def get_detailed_results(self, response):

        pages = response.meta.get("pages", None)
        payloads = response.meta.get("payloads", [])
        unit = response.meta.get("unit", None)
        unit_payloads = response.meta.get("unit_payloads", [])
        pagination_payloads = response.meta.get("pagination_payloads", [])

        selector = self.get_selector(response)

        result_rows = selector.xpath(
            "//tbody[@id='consultaPublicaTabPanel:tabelaDocumentos_data']//tr"
        ) or selector.xpath("//*[@id='consultaPublicaTabPanel:tabelaDocumentos']//tr")

        view_state = selector.xpath(
            "//*[@id='javax.faces.ViewState']/text()"
        ).get()  # noqa

        if not unit:
            unit = selector.xpath(
                "//span[@id='consultaPublicaTabPanel:unidadeJurisdicionadaDecoration:unidadeJurisdicionada']/text()"  # noqa
            ).get()

        if pages is None:
            paginator_text = selector.xpath(
                "//*[@id='consultaPublicaTabPanel:tabelaDocumentos_s']/text()"
            ).get()
            if paginator_text:
                row_count = search(r"rowCount:[0-9]{1,}", paginator_text)
                if row_count:
                    # Because we have 10 results per page
                    row_count = (
                        row_count.group(0).lower().replace("rowcount:", "").strip()
                    )
                    number_of_pages = round(int(row_count) / 10)
                    pages = list(range(1, number_of_pages))

        for row in result_rows:
            columns = row.xpath("./td")
            texts = [
                text.strip()
                for text in columns.xpath(".//text()").extract() or []
                if text.strip()
            ]

            item = DocumentItem(
                category=texts[0],
                filename=f"{uuid4()}-{self.normalize_text(texts[1].strip())}",
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
                    url=self.SEARCH_ENDPOINT,
                    formdata=payload,
                    callback=self.prepare_file_request,
                    meta={
                        "item": item,
                        "payloads": payloads,
                        "pages": pages,
                        "view_state": view_state,
                        "unit": unit,
                        "unit_payloads": unit_payloads,
                        "pagination_payloads": pagination_payloads,
                    },
                    dont_filter=True,
                )
            )

        payload = payloads.pop(0)
        yield FormRequest(**payload)

    def prepare_file_request(self, response):
        yield Request(
            url=self.DOWNLOAD_ENDPOINT,
            callback=self.save_file,
            meta=response.meta,
            dont_filter=True,
        )

    def save_file(self, response):

        item = response.meta["item"]
        payloads = response.meta["payloads"]
        payload = payloads.pop(0) if payloads else None
        pages = response.meta["pages"]
        pagination_payloads = response.meta["pagination_payloads"]

        unit_payloads = response.meta["unit_payloads"]

        files_dir = self.get_files_dir(item)

        with open(f"{files_dir}{item['filename']}", "wb") as fp:  # noqa
            fp.write(response.body)

        for value in (item, payload):
            if isinstance(value, DocumentItem):
                yield value
            else:
                if value:
                    yield FormRequest(**value)
                else:
                    if pages:
                        view_state = response.meta["view_state"]
                        unit = response.meta["unit"]

                        page = pages.pop(0)

                        payload = {
                            "javax.faces.partial.ajax": "true",
                            "javax.faces.source": "consultaPublicaTabPanel:tabelaDocumentos",  # noqa
                            "javax.faces.partial.execute": "consultaPublicaTabPanel:tabelaDocumentos",  # noqa
                            "javax.faces.partial.render": "consultaPublicaTabPanel:tabelaDocumentos",  # noqa
                            "consultaPublicaTabPanel:tabelaDocumentos": "consultaPublicaTabPanel:tabelaDocumentos",  # noqa
                            "consultaPublicaTabPanel:tabelaDocumentos_pagination": "true",  # noqa
                            "consultaPublicaTabPanel:tabelaDocumentos_first": str(
                                page * 10
                            ),
                            "consultaPublicaTabPanel:tabelaDocumentos_rows": "10",
                            "consultaPublicaTabPanel:tabelaDocumentos_encodeFeature": "true",  # noqa
                            "j_idt15": "j_idt15",
                            "javax.faces.ViewState": view_state,
                        }

                        yield FormRequest(
                            url=self.SEARCH_ENDPOINT,
                            formdata=payload,
                            meta={
                                "payloads": payloads,
                                "pages": pages,
                                "unit": unit,
                                "unit_payloads": unit_payloads,
                                "pagination_payloads": pagination_payloads
                            },
                            callback=self.get_detailed_results,
                            dont_filter=True,
                        )
                    else:
                        if unit_payloads:
                            unit_payload = unit_payloads.pop(0)
                            yield FormRequest(**unit_payload)
                        elif pagination_payloads:
                            payload = pagination_payloads.pop(0)

                            yield FormRequest(
                                url=self.SEARCH_ENDPOINT,
                                formdata=payload,
                                meta={
                                    "pagination_payloads": pagination_payloads,
                                    "unit_payloads": unit_payloads,
                                },
                                callback=self.paginate_units,
                            )

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

    def get_files_dir(self, item):
        city = self.cidade.strip().lower().replace(" ", "-")

        competencia = [c.strip() for c in self.competencia.split("/") if c]

        category = self.normalize_text(item["category"])
        unit = self.normalize_text(item["unit"])

        if len(competencia) == 1:
            year = competencia[0]
            files_dir = (
                f"{city}{path_separator}{year}{path_separator}{unit}"
                f"{path_separator}{category}{path_separator}"
            )
        else:
            month, year = competencia
            files_dir = (
                f"{city}{path_separator}{year}{path_separator}{month}"
                f"{path_separator}{unit}{path_separator}{category}{path_separator}"
            )

        files_dir = f"{self.settings['FILES_STORE']}{path_separator}{files_dir}"

        Path(files_dir).mkdir(parents=True, exist_ok=True)

        return files_dir

    def normalize_text(self, text):
        return sub(r"[^a-zA-Z0-9\u00C0-\u017F\s\.-]", "", text)
