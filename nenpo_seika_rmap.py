#!/usr/bin/python3

import sys
import re
import time
import datetime
import csv

import requests

class Rmap:
    RMAP_CATEGORY = [
        'profile',
        'published_papers',
        'awards',
        'misc',
        'books_etc',
        'presentations',
        'works',
        'industrial_property_rights',
        'media_coverage',
    ]

    # from ITCannual.sty
    ITC_SEIKA_CATEGORY = [
        '著書',    # 著書／編集
        '発表',    # その他の発表論文
        '査読付',    # 雑誌以外の査読付論文
        '雑誌論文',    # 雑誌論文
        '招待講演',    # 招待講演
        '招待論文',    # 招待論文
        '特許',    # 特許申請／取得
        '特記',    # 特記事項
        '公開',    # 公開ソフトウェア
        '報道',    # 報道関連
        '受賞',    # 受賞関連
    ]

    def __init__(self, user_id, lang='en', date_from=None, date_to=None):
        self.user_id = user_id
        self.base_url = 'https://api.researchmap.jp/{}'.format(user_id)
        self.lang = lang
        self.date_from = None
        if date_from != None:
            self.date_from = datetime.datetime.strptime(date_from, '%Y/%m/%d')
        self.date_to = None
        if date_to != None:
            self.date_to = datetime.datetime.strptime(date_to, '%Y/%m/%d')

    #    def is_available(self):
    #        params = {}
    #        params['format'] = 'json'
    #        try:
    #            res = requests.get(self.base_url, params=params)
    #            res.raise_for_status()
    #            return res.status_code == 200
    #        except Exception as e:
    #            print(e)
    #        return False

    def get_json(self):
        """
        get user achievements from the researchmap
        :return: json data
        """
        rmap_json = dict()
        for rmap_category in self.RMAP_CATEGORY:
            url = "{}/{}".format(self.base_url, rmap_category)
            try:
                res = requests.get(url)
                res.raise_for_status()
                rmap_json[rmap_category] = res.json()
            except Exception as e:
                print(e)
                sys.exit(1)
            time.sleep(0.2)
        return rmap_json

    def __unwrap_name(self, name):
        m = re.match(r'^(.*?), (.*?)$', name)
        if m != None:
            return "%s %s" % (m.group(2), m.group(1))
        return name

    def __unwrap_lang(self, json, lang):
        if len(json) < 1:
            return None
        if lang in json:
            return json[lang]
        else:
            tmp = next(iter(json))
            return json[tmp]

    def __rmap_date(self, date_string):
        date_fmt = ('%Y', '%Y-%m', '%Y-%m-%d')
        #        try:
        #            if datetime.datetime.strptime(date_string, '%Y'):
        #                return None
        #        except ValueError:
        #            pass
        for dfmt in date_fmt:
            try:
                return datetime.datetime.strptime(date_string, dfmt)
            except ValueError:
                pass
        return None

    def __rmap_date_cmp(self, date):
        if date == None:
            return False
        elif self.date_from <= date <= self.date_to:
            return True
        else:
            return False

    def __extract_rmap_items(self, rmap_items, researcher_name, seika_type, func_seika, authors_key_name, date_key_name):
        for rmap_item in rmap_items:
            seika_item = dict()

            # extract seika info
            seika_item['info'] = dict()
            seika_item['info']['seika_type'] = seika_type  # info:seika_type
            seika_item['info']['user_id'] = self.user_id  # info:user_id
            seika_item['info']['researcher_name'] = researcher_name  # info:researcher_name
            seika_item['info']['date'] = rmap_item[date_key_name]  # info:date
            for item_name, func in func_seika['info']:  # info:else
                if item_name in rmap_item:
                    seika_item['info'][item_name] = func(rmap_item[item_name])

            # extract seika body
            seika_item['body'] = dict()
            if authors_key_name not in rmap_item.keys():  # body:name
                seika_item['body']['authors'] = [researcher_name]
            for item_name, func in func_seika['body']:  # body:else
                if item_name in rmap_item:
                    seika_item['body'][item_name] = func(rmap_item[item_name])

            yield seika_item

    def json_to_seika(self, rmap_json):
        """
        make seika items from rmap json data
        :return: seika items
        """
        seika = list()

        researcher_name = "%s %s" % (rmap_json['profile']['given_name']['en'],
                                     rmap_json['profile']['family_name']['en'])

        func_seika = dict()
        authors_key_name = ''
        date_key_name = ''
        for rmap_category in rmap_json:
            if rmap_category == 'profile':
                continue
            elif rmap_category == 'published_papers':
                authors_key_name = 'authors'
                date_key_name = 'publication_date'
                func_seika['info'] = [
                    ('rm:id', lambda x: x),
                    ('published_paper_type', lambda x: x),
                    ('referee', lambda x: x),
                    ('invited', lambda x: x),
                ]
                func_seika['body'] = [
                    ('authors', lambda x: [self.__unwrap_name(p['name']) for p in self.__unwrap_lang(x, self.lang)]),
                    ('paper_title', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('publication_name', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('volume', lambda x: x),
                    ('number', lambda x: x),
                    ('starting_page', lambda x: x),
                    ('ending_page', lambda x: x),
                    ('publication_date', lambda x: x),
                ]
            elif rmap_category == 'awards':
                authors_key_name = 'winners'
                date_key_name = 'award_date'
                func_seika['info'] = [
                    ('rm:id', lambda x: x),
                ]
                func_seika['body'] = [
                    ('winners', lambda x: [self.__unwrap_name(p['name']) for p in self.__unwrap_lang(x, self.lang)]),
                    ('award_name', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('association', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('award_date', lambda x: x),
                ]
            elif rmap_category == 'misc':
                authors_key_name = 'authors'
                date_key_name = 'publication_date'
                func_seika['info'] = [
                    ('rm:id', lambda x: x),
                ]
                func_seika['body'] = [
                    ('authors', lambda x: [self.__unwrap_name(p['name']) for p in self.__unwrap_lang(x, self.lang)]),
                    ('paper_title', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('publication_name', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('volume', lambda x: x),
                    ('number', lambda x: x),
                    ('starting_page', lambda x: x),
                    ('ending_page', lambda x: x),
                    ('publication_date', lambda x: x),
                ]
            elif rmap_category == 'books_etc':
                authors_key_name = 'authors'
                date_key_name = 'publication_date'
                func_seika['info'] = [
                    ('rm:id', lambda x: x),
                ]
                func_seika['body'] = [
                    ('authors', lambda x: [self.__unwrap_name(p['name']) for p in self.__unwrap_lang(x, self.lang)]),
                    ('book_title', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('publisher', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('publication_date', lambda x: x),
                ]
            elif rmap_category == 'presentations':
                authors_key_name = 'presenters'
                date_key_name = 'publication_date'
                func_seika['info'] = [
                    ('rm:id', lambda x: x),
                    ('invited', lambda x: x),
                ]
                func_seika['body'] = [
                    ('presenters', lambda x: [self.__unwrap_name(p['name']) for p in self.__unwrap_lang(x, self.lang)]),
                    ('presentation_title', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('event', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('location', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('address_country', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('publication_date', lambda x: x),
                ]
            elif rmap_category == 'works':
                authors_key_name = 'creators'
                date_key_name = 'from_date'
                func_seika['info'] = [
                    ('rm:id', lambda x: x),
                ]
                func_seika['body'] = [
                    ('creators', lambda x: [self.__unwrap_name(p['name']) for p in self.__unwrap_lang(x, self.lang)]),
                    ('work_title', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('url', lambda x: x),
                    ('from_date', lambda x: x),
                ]
            elif rmap_category == 'industrial_property_rights':
                authors_key_name = 'inventors'
                date_key_name = 'registration_date'
                func_seika['info'] = [
                    ('rm:id', lambda x: x),
                    ('industrial_property_right_type', lambda x: x),
                ]
                func_seika['body'] = [
                    ('inventors', lambda x: [self.__unwrap_name(p['name']) for p in self.__unwrap_lang(x, self.lang)]),
                    ('industrial_property_right_title', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('application_number', lambda x: x),  # 出願番号
                    ('patent_number', lambda x: x),  # 特許番号
                    ('registration_date', lambda x: x),  # 特許登録日
                    #            ('application_date', lambda x: x),  # 出願日
                ]
            elif rmap_category == 'media_coverage':
                authors_key_name = 'authors'
                date_key_name = 'publication_date'
                func_seika['info'] = [
                    ('rm:id', lambda x: x),
                ]
                func_seika['body'] = [
                    ('media_coverage_title', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('publisher', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('event', lambda x: self.__unwrap_lang(x, self.lang)),
                    ('publication_date', lambda x: x),
                ]
            else:
                continue

            for seika_item in self.__extract_rmap_items(rmap_json[rmap_category]['items'], researcher_name,
                                                        rmap_category, func_seika, authors_key_name, date_key_name):
                # check the date
                if self.date_from != None and self.date_to != None:
                    if not self.__rmap_date_cmp(self.__rmap_date(seika_item['info']['date'])):
                        continue
                seika.append(seika_item)
        return seika

    def __bibitem_date(self, date_string):
        date_lang = ''

        if self.lang == 'ja':
            m = re.match(r'^(\d+)-(\d+)-(\d+)$', date_string)
            if m != None:
                date_lang = "%s年%s月%s日" % (m.group(1), m.group(2), m.group(3))
            m = re.match(r'^(\d+)-(\d+)$', date_string)
            if m != None:
                date_lang = "%s年%s月" % (m.group(1), m.group(2))
            m = re.match(r'^(\d+)$', date_string)
            if m != None:
                date_lang = "%s年" % m.group(1)
        else:
            m = re.match(r'^(\d+)-(\d+)-(\d+)$', date_string)
            if m != None:
                dt = datetime.datetime.strptime(date_string, '%Y-%m-%d')
                date_lang = dt.strftime("%-d %b, %Y")
            m = re.match(r'^(\d+)-(\d+)$', date_string)
            if m != None:
                dt = datetime.datetime.strptime(date_string, '%Y-%m')
                date_lang = dt.strftime("%b, %Y")
            m = re.match(r'^(\d+)$', date_string)
            if m != None:
                date_lang = "%s" % m.group(1)

        return date_lang

    def __seika_to_bibitem(self, seika_item):
        result = []
        for key in seika_item['body']:
            if key == 'winners' or key == 'authors' or key == 'presenters' or key == 'creators' or key == 'inventors':
                result.append(", ".join(seika_item['body'][key]))
            elif key == 'publication_date' or key == 'award_date' or key == 'from_date' or key == 'registration_date':
                result.append(self.__bibitem_date(seika_item['body'][key]))
            elif key == 'starting_page':
                continue
            elif key == 'ending_page':
                if 'starting_page' in seika_item['body'] and 'ending_page' in seika_item['body']:
                    pp = 'pp' + seika_item['body']['starting_page'] + '-' + seika_item['body']['ending_page']
                    result.append(pp)
            else:
                result.append(seika_item['body'][key])
        return result

    def __seika_category(self, seika_info):
        category = ''
        if seika_info['seika_type'] == 'published_papers':
            # check the invited flag
            invited = False
            if 'invited' in seika_info:
                invited = seika_info['invited']

            # check the referee flag
            referee = False
            if 'referee' in seika_info:
                referee = seika_info['referee']

            if invited:
                category = '招待論文'
            elif not referee:
                category = '発表'
            elif referee:
                if 'published_paper_type' not in seika_info:
                    category = '査読付'
                elif seika_info['published_paper_type'] == 'scientific_journal':
                    category = '雑誌論文'
                else:
                    category = '査読付'
        elif seika_info['seika_type'] == 'awards':
            category = '受賞'
        elif seika_info['seika_type'] == 'misc':
            category = '発表'
        elif seika_info['seika_type'] == 'books_etc':
            category = '著書'
        elif seika_info['seika_type'] == 'presentations':
            # check the invited flag
            invited = False
            if 'invited' in seika_info:
                invited = seika_info['invited']

            if invited:
                category = '招待講演'
            else:
                category = '特記'
        elif seika_info['seika_type'] == 'works':
            category = '公開'
        elif seika_info['seika_type'] == 'industrial_property_rights':
            # check the IP type
            ip_type = ''
            if 'industrial_property_right_type' in seika_info:
                ip_type = seika_info['industrial_property_right_type']

            if ip_type == 'patent_right':
                category = '特許'
        elif seika_info['seika_type'] == 'media_coverage':
            category = '報道'

        ## DEGUB: raise the error if category cannot be found
        #try:
        #    if category == '':
        #        raise ValueError("成果アイテムに該当するカテゴリがありません。Debug dump情報を空閑まで連絡ください。")
        #except ValueError as e:
        #    print("Exception: " + repr(e))
        #    print("Debug dump: ", seika_info)
        #    sys.exit(1)

        return category

    def print_bibitem(self, seika_items):
        """
        print seika_items in bibitem format
        """
        # count seika items
        seika_count =dict()
        for seika_key in self.ITC_SEIKA_CATEGORY:
            seika_count[seika_key] = 0
            for seika_item in seika_items:
                # check the category
                if seika_key != self.__seika_category(seika_item['info']):
                    continue
                # count
                seika_count[seika_key] = seika_count[seika_key] + 1

        # print
        for seika_key in self.ITC_SEIKA_CATEGORY:
            # skip if there are zero items
            if seika_count[seika_key] == 0:
                continue

            # print header
            print("\\begin{%s}{%d}" % (seika_key, seika_count[seika_key]))

            # print body
            for seika_item in seika_items:
                # check the category
                if seika_key != self.__seika_category(seika_item['info']):
                    continue

                # print a item
                #print(seika_item)
                bib_label = "%s%s" % (seika_item['info']['user_id'], seika_item['info']['rm:id'])
                print("\\bibitem{%s}" % (bib_label))
                print(", ".join(self.__seika_to_bibitem(seika_item)), end='.\n\n')

            # print footer
            print("\\end{%s}" % (seika_key), end='\n\n')


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        print("usage: python3 %s <input_rmap_users.csv>" % args[0])
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, 'r') as f:
        seika_items = list()

        csvf = csv.reader(f, quotechar='"', skipinitialspace=True)
        for item in csvf:
            rmap_id = ''
            output_lang = 'en'
            date_from = None
            date_to = None
            if len(item) == 1:
                rmap_id = item[0]
            elif len(item) == 2:
                rmap_id = item[0]
                output_lang = item[1]
            elif len(item) == 4:
                rmap_id = item[0]
                output_lang = item[1]
                date_from = item[2]
                date_to = item[3]
            else:
                print("csv format: <rmap_id>, <lang: en>, <date_from: \"2021/4/1\">, <date_to: \"2022/3/1\">")
                sys.exit(1)

            rmap = Rmap(rmap_id, output_lang, date_from, date_to)

            rmap_json = rmap.get_json()
            #import json
            #print(json.dumps(rmap_json, indent=2))

            seika_items.extend(rmap.json_to_seika(rmap_json))
            #for item in seika_items:
            #   print(item)

        rmap.print_bibitem(seika_items)
        time.sleep(1)
