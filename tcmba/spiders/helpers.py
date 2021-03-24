import unicodedata


def format_city(city):
    limit = 30
    if city is None or len(city) > limit:
        raise Exception("Nome de cidade inválido.")
    city = city.strip().upper()
    return city.ljust(limit)


def strip_accents(string):
    if string is None:
        return
    return "".join(
        char
        for char in unicodedata.normalize("NFD", string)
        if unicodedata.category(char) != "Mn"
    )


def format_period(string):
    return string.strip().title()


def format_month_and_year(string):
    return string.strip()


def format_year(year):
    limit = 7
    if year is None or len(year) > limit:
        raise Exception("Ano inválido.")
    year = year.strip()
    return year.ljust(limit)
