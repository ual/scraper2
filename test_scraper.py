# This is a test script for the rental listing scraper
from datetime import datetime as dt
from datetime import timedelta
import pandas as pd
import sys
sys.path.insert(0, 'scraper2/')
import scraper2

__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 6, 2016"


# add subfolder to system path

domains = pd.read_csv('domains.txt', header=None, names=['domain'])
domains = list(domains.domain)
lookback = 2  # hours

s = scraper2.RentalListingScraper(
    domains=domains,
    earliest_ts=dt.now() - timedelta(hours=lookback),
    latest_ts=dt.now() + timedelta(hours=0))

s.run()
