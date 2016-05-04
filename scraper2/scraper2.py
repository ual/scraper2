__author__ = "Sam Maurer, UrbanSim Inc"
__date__ = "May 4, 2016"

from lxml import html
import requests


# Some defaults
DOMAINS = ['http://atlanta.craigslist.org']
OUTFILE = 'test.csv'


class RentalListingScraper(object):

	def __init__(
			self, 
			domains = DOMAINS, 
			outfile = OUTFILE):
		
		self.domains = domains
		self.outfile = outfile


	def _extract(self, list):
		'''
		The xpath() function returns a list of items that may be empty. Most of the time,
		we want the first of any strings that match the xml query. This helper function
		returns that string, or null if the list is empty.
		'''
		
		if len(list) > 0:
			return list[0]
			
		return ''
	

	def _readFromListing(self, item):
	
		pid = item.xpath('@data-pid')[0]  # post id
	
		# Extract two lines of listing info
		line1 = item.xpath('span[@class="txt"]/span[@class="pl"]')[0]
		line2 = item.xpath('span[@class="txt"]/span[@class="l2"]')[0]
	
		dt = line1.xpath('time/@datetime')[0]
		url = 'http://craigslist.org' + line1.xpath('a/@href')[0]
		title = self._extract(line1.xpath('a/span/text()'))
	
		price = line2.xpath('span[@class="price"]/text()')[0].strip('$')
		neighb = line2.xpath('span[@class="pnr"]/small/text()')[0].strip(' ()')
		bedsqft = line2.xpath('span[@class="housing"]/text()')[0]
	
		beds = 0  # Bedrooms - appears as "1br" to "8br" or missing
		for s in bedsqft.split(' '):
			if 'br' in s:
				beds = s.strip('br')
	
		sqft = 0  # Square footage - appears as "000ft" or missing
		for s in bedsqft.split(' '):
			if 'ft' in s:
				sqft = s.strip('ft')

		return [pid, dt, url, title, price, neighb, beds, sqft]

	
	def run(self):
		
		for domain in self.domains:

			page = requests.get(domain + '/search/apa')
			tree = html.fromstring(page.content)

			# Each listing on the search results page is labeled as <p class="row">
			listings = tree.xpath('//p[@class="row"]')

			for item in listings[:2]:
				print self._readFromListing(item)
				# add source when saving
				
			# Go to the next search results page
			
			
				
		return



# stop traversing pages if post id is too old? - or only keep prev calendar day?


