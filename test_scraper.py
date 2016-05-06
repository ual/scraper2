__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 4, 2016"

# This is a test script for the rental listing scraper

import datetime as dt

# add subfolder to system path
import sys
sys.path.insert(0, 'scraper2/')

import scraper2


domains = ['http://atlanta.craigslist.org']

s = scraper2.RentalListingScraper(
		domains = domains,
		earliest_ts = dt.datetime.now() + dt.timedelta(hours=2),
		latest_ts = dt.datetime.now() + dt.timedelta(hours=3))

s.run()