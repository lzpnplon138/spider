# -*- encoding: utf-8 -*-


import sys
import os

from scrapy.cmdline import execute

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# scrapy crawl jobbole
execute(['scrapy', 'crawl', 'jobbole'])
