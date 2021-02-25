from os import makedirs, path

BOT_NAME = "tcmba"

SPIDER_MODULES = ["tcmba.spiders"]
NEWSPIDER_MODULE = "tcmba.spiders"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"  # noqa

ROBOTSTXT_OBEY = False

_current_dir = path.dirname(path.abspath(__file__))
files_dir = _current_dir + "/files"

# Verify if directory exists
if not path.isdir(files_dir):  # create if not
    makedirs(files_dir)

FILES_STORE = files_dir
