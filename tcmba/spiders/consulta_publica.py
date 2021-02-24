from scrapy import Spider, Request, FormRequest
from parsel import Selector
from tcmba.items import DocumentItem
from re import search


class ConsultaPublicaSpider(Spider):
    name = "consulta_publica"
    start_urls = ["https://e.tcm.ba.gov.br/epp/ConsultaPublica/listView.seam"]

    def parse(self, response):
        form_id = "consultaPublicaTabPanel:consultaPublicaPCSearchForm"

        payload = {
            f"{form_id}:PeriodicidadePC_input": "Anual",
            f"{form_id}:competenciaPC_input": "2019   ",
            f"{form_id}:municipio_input": "FEIRA DE SANTANA              ",
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

        """
        Index 9 não tem paginação OK.
        Index 8 contém 6 páginas
        """

        # TODO: Parsear todos os resultados
        for table_row in [result_rows[8]]:
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

        pages = response.meta.get("pages", None)
        payloads = response.meta.get("payloads", [])
        unit = response.meta.get("unit", None)

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
                    meta={
                        "item": item,
                        "payloads": payloads,
                        "pages": pages,
                        "view_state": view_state,
                        "unit": unit,
                    },
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
        pages = response.meta["pages"]

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
                else:
                    if pages:
                        view_state = response.meta["view_state"]
                        unit = response.meta["unit"]

                        page = pages.pop(0)

                        payload = {
                            "javax.faces.partial.ajax": "true",
                            "javax.faces.source": "consultaPublicaTabPanel:tabelaDocumentos",
                            "javax.faces.partial.execute": "consultaPublicaTabPanel:tabelaDocumentos",
                            "javax.faces.partial.render": "consultaPublicaTabPanel:tabelaDocumentos",
                            "consultaPublicaTabPanel:tabelaDocumentos": "consultaPublicaTabPanel:tabelaDocumentos",
                            "consultaPublicaTabPanel:tabelaDocumentos_pagination": "true",
                            "consultaPublicaTabPanel:tabelaDocumentos_first": str(
                                page * 10
                            ),
                            "consultaPublicaTabPanel:tabelaDocumentos_rows": "10",
                            "consultaPublicaTabPanel:tabelaDocumentos_encodeFeature": "true",
                            "j_idt15": "j_idt15",
                            "javax.faces.ViewState": view_state,
                        }

                        yield FormRequest(
                            url="https://e.tcm.ba.gov.br/epp/ConsultaPublica/listView.seam",  # noqa
                            formdata=payload,
                            meta={"payloads": payloads, "pages": pages, "unit": unit},
                            callback=self.get_detailed_results,
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
