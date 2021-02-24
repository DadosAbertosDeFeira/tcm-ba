from scrapy import Spider, Request, FormRequest
from parsel import Selector
from tcmba.items import TcmbaItem


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

            item = TcmbaItem(
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

        # hacky way
        for _ in [item, payload]:
            if isinstance(_, TcmbaItem):
                yield _
            else:
                if _:
                    yield FormRequest(**_)

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
