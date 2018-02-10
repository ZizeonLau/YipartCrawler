from scrapy import Selector
from scrapy.spiders import CrawlSpider
from scrapy.http import Request
import urllib.parse as urlparse
import json
import regex


class yiparts(CrawlSpider):
    name = "yiparts"
    #allowed_domains = ["app.yiparts.com"]
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
                'm1name': m1.get('name'),'m1id': m1.get('id')})

    def parse_m2(self, response):
        m2json = json.loads(response.body_as_unicode())
        metadict = response.meta
        for m2 in m2json:
            url = response.url
            level3dict = {'pid': m2.get('id'), 'level': 3, 'bid': metadict.get('bid'), 'makeid': metadict.get('makeid')}
            body = urlparse.urlencode(level3dict)
            m2name = m2.get('name').replace("&nbsp;", "")
            yield Request(url=url, headers=metadict.get('headers'), body=body, method='POST',
                callback=self.parse_m3, meta={'partjson': response.meta.get('partjson'), 'brandname': metadict.get('brandname'), 'makename': metadict.get('makename'),
                'm1name': metadict.get('m1name'),'m1id': metadict.get('m1id'), 'm2name': m2name,'m2id': m2.get('id'),
                'bid':metadict.get('bid'),'makeid':metadict.get('makeid')})

    def parse_m3(self, response):
        m3json = json.loads(response.body_as_unicode())
        metadict = response.meta
        for m3 in m3json:
            url = 'http://app.yiparts.com/index.php/Product/GetYpcM3?m3id='
            url = url + str(m3.get('id'))
            m3name = '%s%s' % (m3.get('name'), m3.get('id'))
            yield Request(url=url, meta={'partjson': response.meta.get('partjson'), 'brandname': metadict.get('brandname'), 'makename': metadict.get('makename'),
                'm1name': metadict.get('m1name'), 'm2name': metadict.get('m2name'), 'm3name': m3name,
                'm1id': metadict.get('m1id'), 'm2id': metadict.get('m2id'), 'm3id': m3.get('id'), 'bid':metadict.get('bid')
                , 'makeid':metadict.get('makeid'), 'bid':metadict.get('bid'), 'm3url': url},callback=self.parse_part)

    def parse_part(self, response):
        metadict = response.meta
        thepartjson = json.loads(response.body_as_unicode())
        thepart = thepartjson.get('partids')
        partidlist = thepart.split(',')
        partjson = response.meta.get('partjson')
        bid = metadict.get('bid')
        makeid = metadict.get('makeid')
        m1id = metadict.get('m1id')
        m2id = metadict.get('m2id')
        m3id = metadict.get('m3id')
        for part_json in partjson:
            for partid in partidlist:
                if str(part_json.get('id')) == str(partid):
                    if response :
                        #part['partKind'].append({part_json.get('name'): part_json.get('word')})
                        url = 'http://m.yiparts.com/index.php/Product/Search?type=all&vin=&oem=&bid=%s&makeid=%s&m1=%s&m2=%s&m3=%s&partid=%s&by=' % (bid, makeid, m1id, m2id, m3id, partid)
                        yield Request(url=url, method='GET', meta={'partjson': response.meta.get('partjson'), 'brandname': metadict.get('brandname'), 'makename': metadict.get('makename'),
                    'm1name': metadict.get('m1name'), 'm2name': metadict.get('m2name'), 'm3name': metadict.get('m3name'),
                    'm1id': metadict.get('m1id'), 'm2id': metadict.get('m2id'), 'm3id': metadict.get('m3id'),'bid':metadict.get('bid')
                    ,'makeid':metadict.get('makeid'),'bid':metadict.get('bid'),'partname':part_json.get('name'), 'partid': partid, 'm3url': metadict.get('m3url')},
                            callback=self.parse_partlist_1, dont_filter=True)

    def parse_partlist_1(self, response):
        metadict = response.meta
        sel = Selector(response)
        partxpath = sel.xpath('//div/div[@class="list_title panel-heading"]/a')
        partlist=[]
        for thepart in partxpath:
            Thepartname = thepart.xpath('./text()').extract_first()
            #Thepartxpath = thepart.xpath('./@onclick').extract_first()
            #partr = r'ShowTcdProduct\((\d+)\)'
            #partc = regex.search(partr, Thepartxpath)   
            #partid = partc.group(1)
            partlist.append(Thepartname)
        m1id = metadict.get('m1id')
        m2id = metadict.get('m2id')
        m3id = metadict.get('m3id')
        partid = metadict.get('partid')
        page = 2 
        secondurl = 'http://m.yiparts.com/index.php/Product/AjaxSearch?type=all&makeid=&m1=%s&m2=%s&m3=%s&partid=%s&keyword=&oem=&vin=&page=%s&by=oth' % (m1id, m2id, m3id, partid, page)
        yield Request(url=secondurl, method='GET', meta={'partjson': response.meta.get('partjson'), 'brandname': metadict.get('brandname'), 'makename': metadict.get('makename'),
            'm1name': metadict.get('m1name'), 'm2name': metadict.get('m2name'), 'm3name': metadict.get('m3name'),
            'm1id': metadict.get('m1id'), 'm2id': metadict.get('m2id'), 'm3id': metadict.get('m3id'),'bid':metadict.get('bid')
            , 'makeid':metadict.get('makeid'), 'page':page, 'partid':partid, 'partname': metadict.get('partname'), 'partlist': partlist, 'm3url': metadict.get('m3url')},
                    callback=self.parse_partlist_2, dont_filter=True)
        

    def parse_partlist_2(self, response):
        metadict = response.meta
        if response.body_as_unicode():
            m1id = metadict.get('m1id')
            m2id = metadict.get('m2id')
            m3id = metadict.get('m3id')
            partid = metadict.get('partid')
            page = metadict.get('page')
            sel = Selector(response)
            partxpath = sel.xpath('//div/a')
            page = page + 1
            partlist = metadict.get('partlist')
            for part in partxpath:
                Thepartname = part.xpath('./text()').extract_first()
                partlist.append(Thepartname)
            secondurl = 'http://m.yiparts.com/index.php/Product/AjaxSearch?type=all&makeid=&m1=%s&m2=%s&m3=%s&partid=%s&keyword=&oem=&vin=&page=%s&by=oth' % (m1id, m2id, m3id, partid, page)
            yield Request(url=secondurl, method='GET', meta={'partjson': response.meta.get('partjson'), 'brandname': metadict.get('brandname'), 'makename': metadict.get('makename'),
                    'm1name': metadict.get('m1name'), 'm2name': metadict.get('m2name'), 'm3name': metadict.get('name'),
                    'm1id': metadict.get('m1id'), 'm2id': metadict.get('m2id'), 'm3id': metadict.get('m3id'),'bid':metadict.get('bid')
                    ,'makeid':metadict.get('makeid'),'bid':metadict.get('bid'),'page':page, 'partid':partid, 'partname': metadict.get('partname'), 'partlist': partlist, 'm3url': metadict.get('m3url')},
                            callback=self.parse_partlist_2, dont_filter=True)
        else :
            part={}
            part['brand'] = metadict.get('brandname')
            part['corperation'] = metadict.get('makename')
            part['series'] = metadict.get('m1name')
            part['car'] = metadict.get('m2name')
            part['carInfo'] = metadict.get('m3name')
            part['m3url'] = metadict.get('m3url')
            part[metadict.get('partname')] = metadict.get('partlist')
            yield(part)