# This is a test script for the rental listing scraper
from datetime import datetime as dt
from datetime import timedelta
import sys
sys.path.insert(0, 'scraper2/')
import scraper2
import csv

__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 6, 2016"


# add subfolder to system path

domains = []
with open('domains.txt', 'rb') as f:
    for line in f.readlines():
        domains.append((line.strip()))

lookback = 1  # hours

s = scraper2.RentalListingScraper(
    domains=domains,
    earliest_ts=dt.now() - timedelta(hours=lookback),
    latest_ts=dt.now() + timedelta(hours=0))

out = s.run()