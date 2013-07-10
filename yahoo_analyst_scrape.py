import urllib2
from bs4 import BeautifulSoup
import time
import MySQLdb
import argparse

#url stuff
PREFIX_URL = 'http://finance.yahoo.com/q/ao?s='
SUFFIX_URL = '+Analyst+Opinion'
NUM_RETRIES = 10
#ticker stuff
TICKER_FILE = 'tf.txt'
TICKERS = []
LAST_TICKER_FILE = 'lt.txt'
START_LAST_TICKER = True
LAST_INDEX = 0
#company infos
BROKER_RELEVANCE_THRESHOLD = 5
COMPANIES = {}
TD_VALUES = { \
			'No. of Brokers:': 'num_brokers', \
			'High Target:': 'high', \
			'Median Target:': 'median', \
			'Mean Target:': 'mean', \
			'Low Target:': 'low' \
			}
#db info
USERNAME = 'admin'
PASSWORD = 'password'
HOSTNAME = 'localhost'
DBNAME   = 'stock'
DB_BATCH_COUNT = 5

"""
The company class is a convenient wrapper for company information storage

"""
class Company():
	def __init__(self, name, ticker, info):
		self.name = name
		self.ticker = ticker
		self.num_brokers = int(info['num_brokers'])
		self.high = info['high']
		self.mean = info['mean']
		self.median = info['median']
		self.low = info['low']
		self.cur = info['cur']
		self.csv_list_dump = [ \
							  self.ticker, \
							  self.name, \
							  str(int(self.num_brokers)), \
							  str(self.high), \
							  str(self.mean), \
							  str(self.median),  \
							  str(self.low), \
							  str(self.cur), \
							  str(self.low > self.cur), \
							  str(self.num_brokers > BROKER_RELEVANCE_THRESHOLD) \
							  ]
	#tells if a stock is undervalued if current price is less than the low price
	#This means that the most pessimistic broker is optimistic
	def is_undervalued(self):
		if self.low > self.cur:
			return "True"
		else:
			return "False"

	#a stock is only relevant if there are more than 5 brokers covering it
	def is_relevant(self):
		if self.num_brokers > BROKER_RELEVANCE_THRESHOLD:
			return "True"
		else:
			return "False"

	#prints in csv file format
	def csv_dump(self):
		if self.csv_list_dump:
			print ','.join(self.csv_list_dump)
"""
Scrapes yahoo finance for relevant information
"""
def populate_information():
	global TICKERS
	global LAST_INDEX

	#################### AUX METHODS ####################
	#helper method that finds if a td element has info we need
	def is_number(s):
	    try:
	        float(s)
	        return True
	    except ValueError:
	        return False

	def contains_info(td):
		if (not td) or (not td.string):
			#print('Error null td')
			return False
		
		is_true = False
		for value in TD_VALUES.keys():
			if value in td.string:
				is_true = True
		return is_true

	#finds full company name
	def find_name(soup, ticker):
		name_element = soup.find('div', { 'class' : 'title' })
		if name_element and name_element.h2 and name_element.h2.contents:
			name = str(name_element.h2.string)
			if ticker in name:
				return name
		print('Error finding name for: ' + ticker)

	#finds the current stock price of the company
	def find_cur(soup, ticker):
		cur_element = soup.find('span', { 'class' : 'time_rtq_ticker' })
		if cur_element and cur_element.span and cur_element.span.contents:
			cur = cur_element.span.string
			return cur
		print('Error finding current price ' + ticker)

	#finds the mean, median, high, low and num brokers
	def  find_info_map(soup):
		info_map = {}

		tds = soup.findAll('td', { 'class' : 'yfnc_tablehead1' })
		if not tds:
			print('Error no tds of class yfnc_tablehead1')
			return
		#random child will be a <td> node with value mean, median, mode, etc and neighbor with the numeric value
		#we want to go up two levels to the <tr> level and find all its neighbors and their <td> values
		#ie: <tr>
		#      <td scope="row" class="yfnc_tablehead1">Mean Target:</td>
		#      <td class="yfnc_tabledata1">199.92</td>
		#    </tr>
		#    <tr>
		#      <td scope="row" class="yfnc_tablehead1">Median Target:</td>
		#      <td class="yfnc_tabledata1">200.00</td>
		#    </tr>
		#	 <tr>
		#		<td scope="row" class="yfnc_tablehead1">High Target:</td>
		#		<td class="yfnc_tabledata1">218.00</td>
		#	 </tr>
		#	 <tr>
		#		<td scope="row" class="yfnc_tablehead1">Low Target:</td>
		#		<td class="yfnc_tabledata1">170.00</td>
		#	 </tr>
		#	 <tr>
		#		<td scope="row" class="yfnc_tablehead1">No. of Brokers:</td>
		#		<td class="yfnc_tabledata1">22</td>
		#	 </tr>

		for td in tds:
			if not contains_info(td):
				continue

			upper_node = td.parent
			if not upper_node:
				print('Error no upper node for ' + td)
				continue

			#Assuming serial order as sepcified above
			info_key = None
			info_value = None
			for child in upper_node.children:
				if info_key:
					if not is_number(child.string.replace(',','')):
						continue 
					info_value = float(child.string.replace(',',''))
					info_map[TD_VALUES[info_key]] = info_value
					info_key = None
					info_value = None
					continue				
				for key in TD_VALUES.keys():
					if child.string in key:
						info_key = key
						break
		return info_map
		#################### AUX METHODS ####################
	
	# companies list for batching
	companies = [] 

	#start from last ticker by reading last ticker file
	if START_LAST_TICKER:
		f = open(LAST_TICKER_FILE, 'r')
		line = f.readline()
		if line:
			LAST_INDEX = int(line.split('\n')[0])
		else:
			LAST_INDEX = 0
		TICKERS = TICKERS[LAST_INDEX:]

	for ticker in TICKERS:
		#make requests
		url = PREFIX_URL + ticker + SUFFIX_URL
		try:
			print("URL: " + url)
			req_obj = urllib2.urlopen(url).read()
		except IOError:
			print('Error opening request for: ' + ticker)
			continue
		if not req_obj:
			print('Error req_obj null, request to ' + url + ' failed, retrying')
			continue

		#soupify!
		soup = BeautifulSoup(req_obj)
		if not soup:
			print('Error failed to soupify for ' + url)
			continue

		#if the len of soup is == 3, this means beautiful soup crashed, we need to retry the request
		"""
		retries = 0
		while len(soup) < 8 and retries < NUM_RETRIES:
			print("SOUP LENGTH" + str(len(soup)))
			retries = retries + 1
			req_obj = urllib2.urlopen(url).read()
			soup = BeautifulSoup(req_obj)
			if retries > 1:
				print('Retrying request to ' + ticker)
		"""

		#find relevant information
		name = find_name(soup, ticker)
		cur = find_cur(soup, ticker)
		info_map = find_info_map(soup)
		if not info_map:
			print('Error no info_map for: ' + ticker)
			continue
		if not cur:
			print('Error could not find current stock price: ' + ticker)
			continue
		info_map['cur'] = float(cur.replace(',',''))
		if len(info_map) != 6:
			print('Error malformed info_map, length of: ' + str(len(info_map)) + ' for: ' + ticker)
			continue

		COMPANIES[ticker] = Company(name, ticker, info_map)
		companies.append(COMPANIES[ticker])
		COMPANIES[ticker].csv_dump()

		#writing batches to database
		if len(companies) > DB_BATCH_COUNT:
			insert_into_stock_table(companies)
			
			#write last ticker to file to pick up from where we started
			f = open(LAST_TICKER_FILE,'w')
			f.write(str(TICKERS.index(ticker) + LAST_INDEX))
			companies = []

"""
Reads in the ticker values from ticker file, will be well formed
"""
def get_tickers():
	tf = open(TICKER_FILE, 'r')

	#get all the tickers
	while True:
		line = tf.readline()
		if not line:
			break
		#split because tickers are in form
		#\u'tcker_name\n'
		TICKERS.append(line.split('\n')[0])


####################DB STUFF####################
def print_stock_info():
	# Open database connection
	db = MySQLdb.connect(HOSTNAME, USERNAME, PASSWORD, DBNAME)

	# prepare a cursor object using cursor() method
	cursor = db.cursor()

	# execute SQL query using execute() method.
	cursor.execute('SELECT VERSION()')

	# Fetch a single row using fetchone() method.
	data = cursor.fetchone()

	print 'Database version : %s ' % data

	# disconnect from server
	db.close()

def create_tables():
	# Open database connection
	db = MySQLdb.connect(HOSTNAME, USERNAME, PASSWORD, DBNAME)

	# prepare a cursor object using cursor() method
	cursor = db.cursor()

	# Drop table if it already exist using execute() method.
	cursor.execute('DROP TABLE IF EXISTS STOCK')

	# Create table as per requirement
	sql = """CREATE TABLE STOCK 
			(
	         ticker CHAR(4) NOT NULL PRIMARY KEY,
	         cname CHAR(96) NOT NULL,
	         num_brokers INT NOT NULL,
	         high FLOAT NOT NULL,
	         mean FLOAT NOT NULL,
	         median FLOAT NOT NULL,
	         low FLOAT NOT NULL,
	         cur FLOAT NOT NULL,
	         is_undervalued CHAR(8) NOT NULL,
	         is_relevant CHAR(8) NOT NULL
	         )"""

	cursor.execute(sql)
	print('Executing command: ' + sql)
	# disconnect from server
	db.close()

def insert_into_stock_table(companies):
	# Open database connection
	db = MySQLdb.connect(HOSTNAME, USERNAME, PASSWORD, DBNAME)

	# prepare a cursor object using cursor() method
	cursor = db.cursor()

	# Prepare SQL query to INSERT a record into the database.
	for cmpy in companies:
		sql = "REPLACE INTO STOCK(ticker, cname, num_brokers, high, mean, median, low, cur, is_undervalued, is_relevant) \
		        VALUES ('%s', '%s', '%d', '%f', '%f', '%f', '%f', '%f', '%s', '%s' )" \
		       % (cmpy.ticker, cmpy.name, cmpy.num_brokers, cmpy.high, cmpy.mean, cmpy.median, cmpy.low, cmpy.cur, cmpy.is_undervalued(), cmpy.is_relevant())
		try:
		  	# Execute the SQL command
		    cursor.execute(sql)
		    print('Executing command: ' + sql)
		    # Commit your changes in the database
		    db.commit()
		except:
		    # Rollback in case there is any error
		    print('SQL command fails: ' + sql)
		    db.rollback()

	# disconnect from server
	db.close()
####################DB STUFF####################

####################CLI#########################
def cli():
	global LAST_INDEX
	global START_LAST_TICKER
	parser = argparse.ArgumentParser(description='Find great ways to lose money! Find Yahoo Finance\'s analysts\' opinions on lows, high, and currently performing stock prices')
	parser.add_argument('-s', type=int, dest='start', choices=range(5200), \
						help='0 for starting over, or # where to start')
	parser.add_argument('-l', dest='last', type=bool, default=True, nargs='?', \
						help='if last, will read off where the script left off')
	args = parser.parse_args()
	
	if args and args.start:
		LAST_INDEX = args.start
		START_LAST_TICKER = False
	else:
		START_LAST_TICKER = True
	print(args)
####################CLI#########################


def main():
	#create_tables()
	cli()
	print_stock_info()
	get_tickers()
	populate_information()



if __name__ == '__main__':
    main()