import urllib2
import json

SCIN_URL = 'http://eat1-app535.stg.linkedin.com:11454/pinot-senseidb/resources/statistics?q=statistics&bqlRequest='
ADCLICK_URL = 'http://eat1-app556.stg.linkedin.com:11454/pinot-senseidb/resources/statistics?q=statistics&bqlRequest='

INTERSECT_TARGETING_PARAMS = ['memberFunctions', 'memberIndustries', 'memberRegion', 'memberTitles']
SCIN_TARGETING_PARAMS = ['memberCompanySizes']
ADCLICK_NOTABLE_INFO = ['clickCount', 'creativeId']
INTERSECT_NOTABLE_INFO = ['advertiserId', 'campaignId']

def get_adclick_json():
	for tparam in INTERSECT_TARGETING_PARAMS:
		bql = 'SELECT COUNT(*) GROUP BY ' + tparam + ' TOP 100 LIMIT 0'
		url = 
		req = urllib2.urlopen(url).read()




def main():


if __name__ == '__main__':
    main()