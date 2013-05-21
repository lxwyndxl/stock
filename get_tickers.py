import csv

FILES = ['cl1.csv', 'cl2.csv', 'cl3.csv']


def get_tickers():
	tickers = []
	tf = open('tf.txt', 'w+')
	for cl_file in FILES:
		cl = open(cl_file, 'r')
		cl_csv = csv.reader(cl, delimiter=' ', quotechar='|')
		for row in cl_csv:
			ticker = row[0].split(',')[0].split('\"')[1]
			if ('^' in ticker) or ('/' in ticker) or (len(ticker) > 4):
				continue
			tickers.append(ticker)

	for ticker in tickers:
		tf.write(ticker + '\n')



def main():
	get_tickers()

if __name__ == '__main__':
    main()