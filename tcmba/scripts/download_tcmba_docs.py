import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from scrapy.crawler import CrawlerProcess

from tcmba.scripts.check import check_files_from
from tcmba.spiders.consulta_publica import ConsultaPublicaSpider

logger = logging.getLogger(__file__)
FILES_DIR = f'{os.getenv("AIRFLOW_HOME")}/data'  # FIXME
CITY = "feira-de-santana"


def prepare_environment():
    for month, year in months_and_years(date(2015, 10, 1), date(2020, 9, 1)):
        month = "0" + str(month) if month < 10 else month
        dir = f"{FILES_DIR}/{CITY}/{year}/mensal/{month}"
        os.makedirs(dir, exist_ok=True)


def start_crawl(params):
    dir = f"{FILES_DIR}/{CITY}/{year}/mensal/{month}"
    filepath = f"{dir}/consulta_publica_{month}-{year}.json"
    os.system("rm -rf " + filepath)

    process = CrawlerProcess(
        {
            "FEEDS": {
                Path(filepath): {
                    "format": "json",
                    "fields": None,
                }
            },
            "FILES_STORE": FILES_DIR,
        }
    )

    crawler = process.create_crawler(ConsultaPublicaSpider)
    process.crawl(crawler, {"": "Feira de Santana"})  # FIXME
    process.start()

    stats_dict = crawler.stats.get_stats()
    # FIXME  'spider_exceptions/Exception': 1,
    if stats_dict["finish_reason"] != "finished":
        raise Exception("Falha no crawler.")

    return dir


def check_data(filepath):
    logger.info(f"Checagem de dados.\nDiretório: {filepath}")
    stats = check_files_from(filepath)
    logger.info(stats)
    key = list(stats.keys())[0]
    if stats[key]["count_folder_files"] != stats[key]["count_items"]:
        raise Exception("Esperando por checagem manual.")


def months_and_years(start_date, end_date):
    pairs = []
    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            return [(start_date.month, start_date.year)]
    for year in range(start_date.year, end_date.year + 1):
        for month in range(1, 13):
            if start_date.year == end_date.year:
                if start_date.month < month <= end_date.month:
                    pairs.append((month, year))
            elif year == start_date.year:
                if month > start_date.month:
                    pairs.append((month, year))
            elif year == end_date.year:
                if month <= end_date.month:
                    pairs.append((month, year))
            elif year not in (start_date.year, end_date.year):
                pairs.append((month, year))
    return pairs


def sync_to_s3(month, year, period):
    s3_bucket = f"s3://dadosabertosdefeira/maria-quiteria/files/tcmbapublicconsultation/{year}/{period}/{month}"
    dir = f"{FILES_DIR}/feira-de-santana/{year}/{period}/{month}"

    os.subprocess(f"aws s3 sync {dir} {s3_bucket}")  # FIXME
