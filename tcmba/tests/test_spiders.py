from datetime import date, timedelta

from ..spiders.consulta_publica import ConsultaPublicaSpider
from ..spiders.helpers import (
    format_city,
    format_month_and_year,
    format_period,
    format_year,
)
from ..spiders.obras import ConstructionsSpider


class TestConsultaPublicaSpider:
    def test_default_arguments(self):
        fourthy_days_ago = date.today() - timedelta(days=40)
        fourthy_days_ago = date.strftime(fourthy_days_ago, "%m/%Y")

        spider = ConsultaPublicaSpider()
        assert spider.cidade == format_city("Feira de Santana")
        assert spider.periodicidade == format_period("mensal")
        assert spider.competencia == format_month_and_year(fourthy_days_ago)
        assert spider.unidade == ""

    def test_receive_monthly_period(self):
        spider = ConsultaPublicaSpider(
            cidade="CAMPO ALEGRE DE LOURDES",
            periodicidade="MENSAL",
            competencia="08/2018",
            unidade="Prefeitura Municipal de CAMPO ALEGRE DE LOURDES",
        )
        assert spider.cidade == format_city("CAMPO ALEGRE DE LOURDES")
        assert spider.periodicidade == format_period("mensal")
        assert spider.competencia == format_month_and_year("08/2018")
        assert spider.unidade == "Prefeitura Municipal de CAMPO ALEGRE DE LOURDES"

    def test_receive_yearly_period(self):
        spider = ConsultaPublicaSpider(
            cidade="CAMPO ALEGRE DE LOURDES",
            periodicidade="anual ",
            competencia="2018  ",
            unidade="Prefeitura Municipal de CAMPO ALEGRE DE LOURDES",
        )
        assert spider.cidade == format_city("CAMPO ALEGRE DE LOURDES")
        assert spider.periodicidade == format_period("anual ")
        assert spider.competencia == format_year("2018  ")
        assert spider.unidade == "Prefeitura Municipal de CAMPO ALEGRE DE LOURDES"


class TestConstructionsSpider:
    def test_when_default_arguments_then_initial_year_must_be_current_year(self):
        current_year = date.today().year

        spider = ConstructionsSpider()
        assert spider.ano_inicial == current_year

    def test_when_receive_valid_initial_year_must_be_assigned_as_int(self):
        initial_year = "2018"
        spider = ConstructionsSpider(
            ano_inicial=initial_year,
        )
        assert spider.ano_inicial == int(initial_year)
