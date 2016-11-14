# This is a test script for the rental listing scraper
from datetime import datetime as dt
from datetime import timedelta
import time
import sys
sys.path.insert(0, 'scraper2/')
import scraper2
import csv

__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 6, 2016"


# add subfolder to system path

domains = ['http://chico.craigslist.org/search/apa','http://redding.craigslist.org/search/apa']
# with open('domains.txt', 'rb') as f:
#     for line in f.readlines():
#         domains.append((line.strip()))

lookback = 1  # hours
ts = dt.now().strftime('%Y%m%d-%H%M%S')
st = time.time()
s = scraper2.RentalListingScraper(
    domains=domains,
    earliest_ts=dt.utcnow() - timedelta(hours=lookback),
    latest_ts=dt.utcnow() + timedelta(hours=0),
    fname_ts=ts)

out = s.run()
print("Took {0} seconds".format(time.time() - st))
