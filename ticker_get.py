import csv
import string

FILES = ['cl1.csv', 'cl2.csv', 'cl3.csv']
ALPHABET = list(string.ascii_uppercase) 

def get_tickers():
	tickers = []
	tf = open('tf.txt', 'w+')

	for cl_file in FILES:
		cl = open(cl_file, 'r')
		cl_csv = csv.reader(cl, delimiter=' ', quotechar='|')
		
		#get the ticker symbol
		for row in cl_csv:
			ticker = row[0].split(',')[0].split('\"')[1]
			
			#validation
			for char in list(ticker):
				if not char in ALPHABET:
					continue

			tickers.append(ticker)

	for ticker in tickers:
		print(ticker, file=tf)



def main():
	get_tickers()

if __name__ == '__main__':
    main()