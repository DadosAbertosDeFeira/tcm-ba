import unicodedata


def format_city(city):
    limit = 30
    if city is None:
        return
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
