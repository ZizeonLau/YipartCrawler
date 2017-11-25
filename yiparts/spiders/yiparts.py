from scrapy import Selector
from scrapy.spiders import CrawlSpider
from scrapy.http import Request
import urllib.parse as urlparse
import json
import regex


class yiparts(CrawlSpider):
    name = "yiparts"
    allowed_domains = ["app.yiparts.com"]
    start_urls = ['http://www.yiparts.com/Cache/Js/PartJson.cn.js?ver=2.0.58']

    def parse(self, response):
        partr = r'var PartJson = (\[.*\])'
        parttext = regex.search(partr, response.body_as_unicode())
        if parttext:
            partjson = json.loads(parttext.group(1))
            yield Request(url='http://app.yiparts.com/index.php/Product/GetBrand',
                            callback=self.parse_begin,
                            meta={'partjson': partjson})

    def parse_begin(self, response):
        brandjson = json.loads(response.body_as_unicode())
        headers = {'Host': 'app.yiparts.com',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'http://app.yiparts.com/index.php/Product/Search'}
        url = 'http://app.yiparts.com/index.php/Product/GetMakeByBrand'
        for brand in brandjson:
            brandid = brand.get('id')
            req_dict = {}
            req_dict.setdefault('bid', brandid)
            body = urlparse.urlencode(req_dict)
            yield Request(url=url, headers=headers, body=body, method='POST',
                            callback=self.parse_makeid,
                            meta={'partjson': response.meta.get('partjson'), 'headers': headers, 'brandname': brand.get('name') or '', 'bid': brand.get('id')})

    def parse_makeid(self, response):
        makejson = json.loads(response.body_as_unicode())
        metadict = response.meta
        for make in makejson:
            url = 'http://app.yiparts.com/index.php/Product/GetYpcModel'
            level1dict = {'pid': make.get('id'), 'level': 1, 'bid': metadict.get('bid'), 'makeid': make.get('id')}
            body = urlparse.urlencode(level1dict)
            yield Request(url=url, headers=metadict.get('headers'), body=body, method='POST',
                callback=self.parse_m1, meta={'partjson': response.meta.get('partjson'), 'headers': metadict.get('headers'), 'brandname': metadict.get('brandname'),
                'bid': metadict.get('bid'), 'makeid': make.get('id'), 'makename': make.get('name')})

    def parse_m1(self, response):
        m1json = json.loads(response.body_as_unicode())
        metadict = response.meta
        url = response.url
        for m1 in m1json:
            level2dict = {'pid': m1.get('id'), 'level': 2, 'bid': metadict.get('bid'), 'makeid': metadict.get('makeid')}
            body = urlparse.urlencode(level2dict)
            yield Request(url=url, headers=metadict.get('headers'), body=body, method='POST',
                callback=self.parse_m2, meta={'partjson': response.meta.get('partjson'), 'headers': metadict.get('headers'), 'brandname': metadict.get('brandname'),
                'bid': metadict.get('bid'), 'makeid': metadict.get('makeid'), 'makename': metadict.get('makename'),
                'm1name': m1.get('name')})

    def parse_m2(self, response):
        m2json = json.loads(response.body_as_unicode())
        metadict = response.meta
        for m2 in m2json:
            url = response.url
            level3dict = {'pid': m2.get('id'), 'level': 3, 'bid': metadict.get('bid'), 'makeid': metadict.get('makeid')}
            body = urlparse.urlencode(level3dict)
            yield Request(url=url, headers=metadict.get('headers'), body=body, method='POST',
                callback=self.parse_m3, meta={'partjson': response.meta.get('partjson'), 'brandname': metadict.get('brandname'), 'makename': metadict.get('makename'),
                'm1name': metadict.get('m1name'), 'm2name': m2.get('name')})

    def parse_m3(self, response):
        m3json = json.loads(response.body_as_unicode())
        metadict = response.meta
        for m3 in m3json:
            url = 'http://app.yiparts.com/index.php/Product/GetYpcM3?m3id='
            url = url + str(m3.get('id'))
            yield Request(url=url, meta={'partjson': response.meta.get('partjson'), 'brandname': metadict.get('brandname'), 'makename': metadict.get('makename'),
                'm1name': metadict.get('m1name'), 'm2name': metadict.get('m2name'), 'm3name': m3.get('name')},
                callback=self.parse_part)

    def parse_part(self, response):
        metadict = response.meta
        thepartjson = json.loads(response.body_as_unicode())
        thepart = thepartjson.get('partids')
        partidlist = thepart.split(',')
        partjson = response.meta.get('partjson')

        part = {}
        part['brand'] = metadict.get('brandname')
        part['corperation'] = metadict.get('makename')
        part['series'] = metadict.get('m1name')
        part['car'] = metadict.get('m2name')
        part['carInfo'] = metadict.get('m3name')
        part['partKind'] = []

        for part_json in partjson:
            for partid in partidlist:
                if str(part_json.get('id')) == str(partid):
                    part['partKind'].append({part_json.get('name'): part_json.get('word')})

        yield part
