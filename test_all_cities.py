__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 6, 2016"

# This is a test script for the rental listing scraper

from datetime import datetime as dt
from datetime import timedelta

# add subfolder to system path
import sys
sys.path.insert(0, 'scraper2/')

import scraper2


domains = [
	'http://atlanta.craigslist.org',
	'http://austin.craigslist.org',
	'http://boston.craigslist.org',
	'http://chicago.craigslist.org',
	'http://dallas.craigslist.org',
	'http://denver.craigslist.org',
	'http://detroit.craigslist.org',
	'http://houston.craigslist.org',
	'http://lasvegas.craigslist.org',
	'http://losangeles.craigslist.org',
	'http://miami.craigslist.org',
	'http://minneapolis.craigslist.org',
	'http://newyork.craigslist.org',
	'http://orangecounty.craigslist.org',
	'http://philadelphia.craigslist.org',
	'http://phoenix.craigslist.org',
	'http://portland.craigslist.org',
	'http://raleigh.craigslist.org',
	'http://sacramento.craigslist.org',
	'http://sandiego.craigslist.org',
	'http://seattle.craigslist.org',
	'http://sfbay.craigslist.org',
	'http://washingtondc.craigslist.org']


s = scraper2.RentalListingScraper(
		domains = domains,
		earliest_ts = dt.now() - timedelta(hours=0.25),
		latest_ts = dt.now())

s.run()