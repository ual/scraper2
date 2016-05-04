__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 4, 2016"

import datetime as dt
from lxml import html
import requests


# Some defaults
DOMAINS = ['http://atlanta.craigslist.org']
OUTFILE = 'test.csv'
EARLIEST_TIME = dt.datetime.now() + dt.timedelta(hours=1)
LATEST_TIME = dt.datetime.now() + dt.timedelta(hours=3)


class RentalListingScraper(object):

	def __init__(
			self, 
			domains = DOMAINS, 
			outfile = OUTFILE,
			earliest_time = EARLIEST_TIME,
			latest_time = LATEST_TIME):
		
		self.domains = domains
		self.outfile = outfile
		self.earliest_time = earliest_time
		self.latest_time = latest_time


	def _get_str(self, list):
		'''
		The xpath() function returns a list of items that may be empty. Most of the time,
		we want the first of any strings that match the xml query. This helper function
		returns that string, or null if the list is empty.
		'''
		
		if len(list) > 0:
			return list[0]

		return ''
	
	
	def _get_int_prefix(self, str, label):
		'''
		Bedrooms and square footage have the format "xx 1br xx 450ft xx". This helper 
		function extracts relevant integers from strings of this format.
		'''		
		
		for s in str.split(' '):
			if label in s:
				return s.strip(label)
				
		return 0
		
	

	def _readFromListing(self, item):
		'''
		Note that xpath() returns a list with elements of varying types depending on the
		query results: xml objects, strings, etc.
		'''
	
		pid = item.xpath('@data-pid')[0]  # post id, always present
	
		# Extract two lines of listing info, always present
		line1 = item.xpath('span[@class="txt"]/span[@class="pl"]')[0]
		line2 = item.xpath('span[@class="txt"]/span[@class="l2"]')[0]
	
		dt = line1.xpath('time/@datetime')[0]  # always present
		url = 'http://craigslist.org' + line1.xpath('a/@href')[0]  # always present
		title = self._get_str(line1.xpath('a/span/text()'))
	
		price = self._get_str(line2.xpath('span[@class="price"]/text()')).strip('$')
		neighb = self._get_str(line2.xpath('span[@class="pnr"]/small/text()')).strip(' ()')
		bedsqft = self._get_str(line2.xpath('span[@class="housing"]/text()'))
	
		beds = self._get_int_prefix(bedsqft, "br")  # appears as "1br" to "8br" or missing
		sqft = self._get_int_prefix(bedsqft, "ft")  # appears as "000ft" or missing
		
		return [pid, dt, url, title, price, neighb, beds, sqft]

	
	def run(self):
		
		for domain in self.domains:

			page = requests.get(domain + '/search/apa')
			tree = html.fromstring(page.content)

			# Each listing on the search results page is labeled as <p class="row">
			listings = tree.xpath('//p[@class="row"]')

			for item in listings:
				r = self._readFromListing(item)
				ts = dt.datetime.strptime(r[1], '%Y-%m-%d %H:%M')
				print ts
				
				if (ts > self.latest_time):
					print "too late"
					
				if (ts < self.earliest_time):
					print "too early"
					break
				# add source when saving
				
				
				
			# Go to the next search results page
			
			
				
		return



# stop traversing pages if post id is too old? - or only keep prev calendar day?


