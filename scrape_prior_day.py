__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 6, 2016"

# This is a test script for the rental listing scraper

from datetime import datetime as dt
from datetime import date, time, timedelta

# add subfolder to system path
import sys
sys.path.insert(0, 'scraper2/')

import scraper2


with open('domains.txt', 'rb') as f:
	domains = f.read().splitlines()
	
yesterday24h = dt.combine(date.today(), time.min)
yesterday00h = yesterday24h - timedelta(days=1)

s = scraper2.RentalListingScraper(
		domains = domains,
		fname_base = yesterday00h.strftime('%Y%m%d'),
		earliest_ts = yesterday00h,
		latest_ts = yesterday24h,
		fname_ts = False)

s.run()