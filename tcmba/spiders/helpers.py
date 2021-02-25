import unicodedata


def format_city(city):
    limit = 30
    if city is None or len(city) > limit:
        raise Exception("Nome de cidade inválido.")
    city = strip_accents(city.strip().upper())
    number_of_spaces = limit - len(city)
    return f"{city}{number_of_spaces * ' '}"


def strip_accents(string):
    if string is None:
        return
    return "".join(
        char
        for char in unicodedata.normalize("NFD", string)
        if unicodedata.category(char) != "Mn"
    )


def format_period(string):
    return string.title()


def format_month_and_year(string):
    return string


def format_year(year):
    limit = 7
    if year is None or len(year) > limit:
        raise Exception("Ano inválido.")
    year = year.strip()
    number_of_spaces = limit - len(year)
    return f"{year}{number_of_spaces * ' '}"
