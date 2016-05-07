__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 6, 2016"

# This is a test script for the rental listing scraper

from datetime import datetime as dt
from datetime import timedelta

# add subfolder to system path
import sys
sys.path.insert(0, 'scraper2/')

import scraper2


# Craiglist regions that divide listings into by-owner vs. by-broker use a different 
# URL ending -- 'aap' for 'all apartments' rather than 'apa' for 'apartments'.

domains = [
	'http://atlanta.craigslist.org/search/apa',
	'http://austin.craigslist.org/search/apa',
	'http://boston.craigslist.org/search/aap',
	'http://chicago.craigslist.org/search/apa',
	'http://dallas.craigslist.org/search/apa',
	'http://denver.craigslist.org/search/apa',
	'http://detroit.craigslist.org/search/apa',
	'http://houston.craigslist.org/search/apa',
	'http://lasvegas.craigslist.org/search/apa',
	'http://losangeles.craigslist.org/search/apa',
	'http://miami.craigslist.org/search/apa',
	'http://minneapolis.craigslist.org/search/apa',
	'http://newyork.craigslist.org/search/aap',
	'http://orangecounty.craigslist.org/search/apa',
	'http://philadelphia.craigslist.org/search/apa',
	'http://phoenix.craigslist.org/search/apa',
	'http://portland.craigslist.org/search/apa',
	'http://raleigh.craigslist.org/search/apa',
	'http://sacramento.craigslist.org/search/apa',
	'http://sandiego.craigslist.org/search/apa',
	'http://seattle.craigslist.org/search/apa',
	'http://sfbay.craigslist.org/search/apa',
	'http://washingtondc.craigslist.org/search/apa']


s = scraper2.RentalListingScraper(
		domains = domains,
		earliest_ts = dt.now() - timedelta(hours=0.05),
		latest_ts = dt.now())

s.run()