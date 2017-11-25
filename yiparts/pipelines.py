# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json


class YipartsPipeline(object):
    def process_item(self, item, spider):
        with open('./thecar.json', 'a') as f:
            f.write(json.dumps(item, indent=4, ensure_ascii=False))
        return item
