import pytest

from .helpers import format_city, strip_accents


@pytest.mark.parametrize(
    "city,expected_format",
    [
        ("Feira de Santana", "FEIRA DE SANTANA              "),
        ("campo alegre de lourdes", "CAMPO ALEGRE DE LOURDES       "),
        ("SALVADOR", "SALVADOR                      "),
        ("     Amélia Rodrigues    ", "AMELIA RODRIGUES              "),
        (None, None),
    ],
)
def test_given_city_format_according_to_tcmba_format(city, expected_format):
    assert format_city(city) == expected_format


@pytest.mark.parametrize(
    "original_value,expected_value",
    [
        ("tomada", "tomada"),
        ("pregão presencial", "pregao presencial"),
        ("pregão eletrônico", "pregao eletronico"),
        ("concorrência", "concorrencia"),
        ("çãôéà", "caoea"),
        (None, None),
    ],
)
def test_strip_accents(original_value, expected_value):
    assert strip_accents(original_value) == expected_value
