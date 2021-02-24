from scrapy import cmdline
import sys


def main(name):
    if name:
        return cmdline.execute(name)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print("usage: debug_scrapy.py scrapy <command> [options] [args]")
