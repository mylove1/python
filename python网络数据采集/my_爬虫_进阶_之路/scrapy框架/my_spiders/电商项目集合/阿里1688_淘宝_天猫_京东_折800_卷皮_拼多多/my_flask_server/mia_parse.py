# coding:utf-8

'''
@author = super_fazai
@File    : mia_parse.py
@Time    : 2018/1/13 10:57
@connect : superonesfazai@gmail.com
'''

"""
蜜芽页面采集系统
"""

import time
from random import randint
import json
import requests
import re
from pprint import pprint
from decimal import Decimal
from time import sleep
import datetime
import re
import gc
import pytz
from scrapy import Selector

from settings import HEADERS

class MiaParse(object):
    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            # 'Accept-Encoding:': 'gzip',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'm.mia.com',
            'Referer': 'https://m.mia.com/',
            'User-Agent': HEADERS[randint(0, 34)],  # 随机一个请求头
        }
        self.result_data = {}

    def get_goods_data(self, goods_id):
        '''
        模拟构造得到data的url
        :param goods_id:
        :return: data dict类型
        '''
        if goods_id == '':
            self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
            return {}
        else:
            data = {}
            # 常规商品手机地址
            goods_url = 'https://m.mia.com/item-' + str(goods_id) + '.html'
            # 常规商品pc地址
            # goods_url = 'https://www.mia.com/item-' + str(goods_id) + '.html'
            print('------>>>| 待抓取的地址为: ', goods_url)

            body = self.get_url_body(tmp_url=goods_url)
            # print(body)

            if body == '':
                self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                return {}

            if re.compile(r'_sign_direct_url = ').findall(body) != []:      # 表明是跳转，一般会出现这种情况的是拼团商品
                # 出现跳转时
                try:
                    sign_direct_url = re.compile(r"_sign_direct_url = '(.*?)';").findall(body)[0]
                    print('*** 获取到跳转地址为: ', sign_direct_url)
                except IndexError:
                    sign_direct_url = ''
                    print('获取跳转的地址时出错!')

                body = self.get_url_body(tmp_url=sign_direct_url)

                if re.compile(r'://m.miyabaobei.hk/').findall(sign_direct_url) != []:
                    # 表示为全球购商品
                    print('*** 此商品为全球购商品!')
                    is_hk = True
                else:
                    is_hk = False

            else:
                is_hk = False
                sign_direct_url = ''

            try:
                # 名字
                # var google_tag_params =
                base_info = re.compile(r'var google_tag_params = (.*?);// ]]></script>').findall(body)[0]
                base_info = re.compile(r'//BFD商品页参数开始').sub('', base_info)
                # print(base_info)
                title = re.compile(r'bfd_name : "(.*?)"').findall(base_info)[0]
                # print(title)
                data['title'] = title

                # 子标题
                try:
                    sub_title = Selector(text=body).css('div.titleout div::text').extract_first()

                    if sub_title is None:
                        sub_title = Selector(text=body).css('div.descInfo::text').extract_first()

                        if sub_title is None:
                            sub_title = ''
                except:
                    sub_title = ''
                data['sub_title'] = sub_title
                # print(sub_title)

                '''
                获取所有示例图片
                '''
                if is_hk is True:   # 全球购
                    tmp_url_2 = 'https://www.miyabaobei.hk/item-' + str(goods_id) + '.html'
                else:
                    tmp_url_2 = 'https://www.mia.com/item-' + str(goods_id) + '.html'

                tmp_body_2 = self.get_url_body(tmp_url=tmp_url_2)
                # print(Selector(text=tmp_body_2).css('div.small').extract())

                all_img_url = []
                for item in Selector(text=tmp_body_2).css('div.small img').extract():
                    # print(item)
                    tmp_img_url = Selector(text=item).css('img::attr("src")').extract_first()
                    all_img_url.append({'img_url': tmp_img_url})

                '''
                获取p_info
                '''
                tmp_p_info = Selector(text=body).css('div.showblock div p').extract_first()

                if tmp_p_info == '':
                    print('获取到的tmp_p_info为空值, 请检查!')
                    self.result_data = {}
                    return {}
                else:
                    tmp_p_info = re.compile('<p>|</p>').sub('', tmp_p_info)
                    tmp_p_info = re.compile(r'<!--思源品牌，隐藏品牌-->').sub('', tmp_p_info)
                    p_info = [{'p_name': item.split('：')[0], 'p_value': item.split('：')[1]} for item in tmp_p_info.split('<br>') if item != '']

                # pprint(p_info)
                data['p_info'] = p_info

                # 获取div_desc
                div_desc = Selector(text=body).css('div.showblock div.xq').extract_first()
                if div_desc == '':
                    print('获取到的div_desc为空值! 请检查')
                    self.result_data = {}
                    return {}

                div_desc = re.compile('<!--香港仓特定下展图开始-->|<!--香港仓特定下展图结束-->').sub('', div_desc)
                div_desc = re.compile(r' src=".*?"').sub(' ', div_desc)
                div_desc = re.compile(r'data-src="').sub('src=\"', div_desc)
                # print(div_desc)
                data['div_desc'] = div_desc

                '''
                获取每个规格的goods_id，跟规格名，以及img_url, 用于后面的处理
                '''
                # 颜色规格等
                # var sku_list_info =
                # pc版没有sku_list_info，只在phone的html界面中才有这个
                tmp_sku_info = re.compile('var sku_list_info = (.*?);sku_list_info = ').findall(body)[0]
                # print(tmp_sku_info)

                try:
                    # 看起来像json但是实际不是就可以这样进行替换，再进行json转换
                    tmp_sku_info = str(tmp_sku_info).strip("'<>() ").replace('\'', '\"')

                    tmp_sku_info = json.loads(tmp_sku_info)
                    # print(tmp_sku_info)
                except Exception as e:
                    print('json.loads遇到错误如下: ', e)
                    self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                    tmp_sku_info = {}
                    return {}

                tmp_sku_info = [{'goods_id': item.get('id'), 'color_name': item.get('code_color')} for item in tmp_sku_info.values()]
                # pprint(tmp_sku_info)

                sku_info = []
                for item in tmp_sku_info:
                    if is_hk is True:
                        tmp_url = 'https://www.miyabaobei.hk/item-' + str(goods_id) + '.html'
                    else:
                        tmp_url = 'https://www.mia.com/item-' + item.get('goods_id') + '.html'

                    tmp_body = self.get_url_body(tmp_url=tmp_url)
                    # print(tmp_body)

                    if sign_direct_url != '':
                        # 下面由于html不规范获取不到img_url，所以采用正则
                        # img_url = Selector(text=body).css('div.big.rel img::attr("src")').extract_first()
                        img_url = re.compile(r'<div class="big rel"><img src="(.*?)"width=').findall(tmp_body)[0]
                        # print(img_url)
                    else:
                        img_url = re.compile(r'normal_pic_src = "(.*?)"').findall(tmp_body)[0]

                    sku_info.append({
                        'goods_id': item.get('goods_id'),
                        'color_name': item.get('color_name'),
                        'img_url': img_url,
                    })
                    sleep(.1)
                # pprint(sku_info)

                '''
                由于这个拿到的都是小图，分辨率相当低，所以采用获取每个goods_id的phone端地址来获取每个规格的高清规格图
                '''
                # # print(Selector(text=body).css('dd.color_list li').extract())
                # for item in Selector(text=body).css('dd.color_list li').extract():
                #     # print(item)
                #     try:
                #         # 该颜色的商品的goods_id
                #         color_goods_id = Selector(text=item).css('a::attr("href")').extract_first()
                #         # 该颜色的名字
                #         color_name = Selector(text=item).css('a::attr("title")').extract_first()
                #         # 该颜色的img_url
                #         color_goods_img_url = Selector(text=item).css('img::attr("src")').extract_first()
                #
                #         color_goods_id = re.compile('(\d+)').findall(color_goods_id)[0]
                #     except IndexError:      # 表示该li为这个tmp_url的地址 (单独处理goods_id)
                #         color_goods_id = goods_id
                #         color_name = Selector(text=item).css('a::attr("title")').extract_first()
                #         color_goods_img_url = Selector(text=item).css('img::attr("src")').extract_first()
                #     print(color_goods_id, ' ', color_name, ' ', color_goods_img_url)

                '''
                获取每个规格对应价格跟规格以及其库存
                '''
                goods_id_str = '-'.join([item.get('goods_id') for item in tmp_sku_info])
                # print(goods_id_str)
                tmp_url = 'https://p.mia.com/item/list/' + goods_id_str
                # print(tmp_url)

                tmp_body = self.get_url_body(tmp_url=tmp_url)
                # print(tmp_body)

                try:
                    tmp_data = json.loads(tmp_body).get('data', [])
                    # pprint(tmp_data)
                except Exception as e:
                    print('json.loads转换tmp_body时出错!')
                    tmp_data = []
                    self.result_data = {}
                    return {}

                true_sku_info = []
                i_s = {}
                for item_1 in sku_info:
                    for item_2 in tmp_data:
                        if item_1.get('goods_id') == str(item_2.get('id', '')):
                            i_s = item_2.get('i_s', {})
                            # print(i_s)
                            for item_3 in i_s.keys():
                                tmp = {}
                                if item_3 == 'SINGLE':
                                    spec_value = item_1.get('color_name')
                                else:
                                    spec_value = item_1.get('color_name') + '|' + item_3
                                normal_price = str(item_2.get('mp'))
                                detail_price = str(item_2.get('sp'))
                                img_url = item_1.get('img_url')
                                rest_number = i_s.get(item_3)
                                if rest_number == 0:
                                    pass
                                else:
                                    tmp['spec_value'] = spec_value
                                    tmp['normal_price'] = normal_price
                                    tmp['detail_price'] = detail_price
                                    tmp['img_url'] = img_url
                                    tmp['rest_number'] = rest_number
                                    true_sku_info.append(tmp)
                data['price_info_list'] = true_sku_info
                # pprint(true_sku_info)

                '''
                设置detail_name_list
                '''
                if len(i_s) == 1 or len(i_s) == 0:
                    detail_name_list = [{'spec_name': '可选'}]
                else:
                    detail_name_list = [{'spec_name': '可选'}, {'spec_name': '规格'}]
                data['detail_name_list'] = detail_name_list
                # print(detail_name_list)

                '''单独处理all_img_url为[]的情况'''
                if all_img_url == []:
                    all_img_url = [{'img_url': true_sku_info[0].get('img_url')}]

                data['all_img_url'] = all_img_url
                # pprint(all_img_url)

                '''
                单独处理得到goods_url
                '''
                if sign_direct_url != '':
                    goods_url = sign_direct_url

                data['goods_url'] = goods_url

            except Exception as e:
                print('遇到错误如下: ', e)
                self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                return {}

            if data != {}:
                # pprint(data)
                self.result_data = data
                return data

            else:
                print('data为空!')
                self.result_data = {}  # 重置下，避免存入时影响下面爬取的赋值
                return {}

    def deal_with_data(self):
        '''
        处理得到规范的data数据
        :return: result 类型 dict
        '''
        data = self.result_data
        if data != {}:
            # 店铺名称
            shop_name = ''

            # 掌柜
            account = ''

            # 商品名称
            title = data['title']

            # 子标题
            sub_title = data['sub_title']

            # 商品价格和淘宝价
            try:
                tmp_price_list = sorted([round(float(item.get('detail_price', '')), 2) for item in data['price_info_list']])
                price = tmp_price_list[-1]  # 商品价格
                taobao_price = tmp_price_list[0]  # 淘宝价
            except IndexError:
                self.result_data = {}
                return {}

            # 商品标签属性名称
            detail_name_list = data['detail_name_list']

            # 要存储的每个标签对应规格的价格及其库存
            price_info_list = data['price_info_list']

            # 所有示例图片地址
            all_img_url = data['all_img_url']

            # 详细信息标签名对应属性
            p_info = data['p_info']

            # div_desc
            div_desc = data['div_desc']

            # 用于判断商品是否已经下架
            is_delete = 0

            result = {
                'goods_url': data['goods_url'],         # goods_url
                'shop_name': shop_name,                 # 店铺名称
                'account': account,                     # 掌柜
                'title': title,                         # 商品名称
                'sub_title': sub_title,                 # 子标题
                'price': price,                         # 商品价格
                'taobao_price': taobao_price,           # 淘宝价
                # 'goods_stock': goods_stock,            # 商品库存
                'detail_name_list': detail_name_list,   # 商品标签属性名称
                # 'detail_value_list': detail_value_list,# 商品标签属性对应的值
                'price_info_list': price_info_list,     # 要存储的每个标签对应规格的价格及其库存
                'all_img_url': all_img_url,             # 所有示例图片地址
                'p_info': p_info,                       # 详细信息标签名对应属性
                'div_desc': div_desc,                   # div_desc
                'is_delete': is_delete                  # 用于判断商品是否已经下架
            }
            # pprint(result)
            # print(result)
            # wait_to_send_data = {
            #     'reason': 'success',
            #     'data': result,
            #     'code': 1
            # }
            # json_data = json.dumps(wait_to_send_data, ensure_ascii=False)
            # print(json_data)
            return result

        else:
            print('待处理的data为空的dict, 该商品可能已经转移或者下架')
            return {}

    def insert_into_mia_xianshimiaosha_table(self, data, pipeline):
        data_list = data
        tmp = {}
        tmp['goods_id'] = data_list['goods_id']  # 官方商品id
        tmp['spider_url'] = data_list['goods_url']  # 商品地址

        '''
        时区处理，时间处理到上海时间
        '''
        tz = pytz.timezone('Asia/Shanghai')  # 创建时区对象
        now_time = datetime.datetime.now(tz)
        # 处理为精确到秒位，删除时区信息
        now_time = re.compile(r'\..*').sub('', str(now_time))
        # 将字符串类型转换为datetime类型
        now_time = datetime.datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S')

        tmp['deal_with_time'] = now_time  # 操作时间
        tmp['modfiy_time'] = now_time  # 修改时间

        tmp['shop_name'] = data_list['shop_name']  # 公司名称
        tmp['title'] = data_list['title']  # 商品名称
        tmp['sub_title'] = data_list['sub_title']

        # 设置最高价price， 最低价taobao_price
        try:
            tmp['price'] = Decimal(data_list['price']).__round__(2)
            tmp['taobao_price'] = Decimal(data_list['taobao_price']).__round__(2)
        except:
            print('此处抓到的可能是蜜芽秒杀券所以跳过')
            return None

        tmp['detail_name_list'] = data_list['detail_name_list']  # 标签属性名称

        """
        得到sku_map
        """
        tmp['price_info_list'] = data_list.get('price_info_list')  # 每个规格对应价格及其库存

        tmp['all_img_url'] = data_list.get('all_img_url')  # 所有示例图片地址

        tmp['p_info'] = data_list.get('p_info')  # 详细信息
        tmp['div_desc'] = data_list.get('div_desc')  # 下方div

        tmp['miaosha_time'] = data_list.get('miaosha_time')
        tmp['pid'] = data_list.get('pid')

        # 采集的来源地
        tmp['site_id'] = 20  # 采集来源地(蜜芽秒杀商品)

        tmp['miaosha_begin_time'] = data_list.get('miaosha_begin_time')
        tmp['miaosha_end_time'] = data_list.get('miaosha_end_time')

        tmp['is_delete'] = data_list.get('is_delete')  # 逻辑删除, 未删除为0, 删除为1
        # print('is_delete=', tmp['is_delete'])

        # print('------>>> | 待存储的数据信息为: |', tmp)
        print('------>>>| 待存储的数据信息为: |', tmp.get('goods_id'))

        pipeline.insert_into_mia_xianshimiaosha_table(tmp)

    def update_mia_xianshimiaosha_table(self, data, pipeline):
        data_list = data
        tmp = {}
        tmp['goods_id'] = data_list['goods_id']  # 官方商品id

        '''
        时区处理，时间处理到上海时间
        '''
        tz = pytz.timezone('Asia/Shanghai')  # 创建时区对象
        now_time = datetime.datetime.now(tz)
        # 处理为精确到秒位，删除时区信息
        now_time = re.compile(r'\..*').sub('', str(now_time))
        # 将字符串类型转换为datetime类型
        now_time = datetime.datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S')

        tmp['modfiy_time'] = now_time  # 修改时间

        tmp['shop_name'] = data_list['shop_name']  # 公司名称
        tmp['title'] = data_list['title']  # 商品名称
        tmp['sub_title'] = data_list['sub_title']

        # 设置最高价price， 最低价taobao_price
        try:
            tmp['price'] = Decimal(data_list['price']).__round__(2)
            tmp['taobao_price'] = Decimal(data_list['taobao_price']).__round__(2)
        except:
            print('此处抓到的可能是蜜芽秒杀券所以跳过')
            return None

        tmp['detail_name_list'] = data_list['detail_name_list']  # 标签属性名称

        """
        得到sku_map
        """
        tmp['price_info_list'] = data_list.get('price_info_list')  # 每个规格对应价格及其库存

        tmp['all_img_url'] = data_list.get('all_img_url')  # 所有示例图片地址

        tmp['p_info'] = data_list.get('p_info')  # 详细信息
        tmp['div_desc'] = data_list.get('div_desc')  # 下方div

        tmp['miaosha_time'] = data_list.get('miaosha_time')

        tmp['miaosha_begin_time'] = data_list.get('miaosha_begin_time')
        tmp['miaosha_end_time'] = data_list.get('miaosha_end_time')

        tmp['is_delete'] = data_list.get('is_delete')  # 逻辑删除, 未删除为0, 删除为1
        # print('is_delete=', tmp['is_delete'])

        # print('------>>> | 待存储的数据信息为: |', tmp)
        print('------>>>| 待存储的数据信息为: |', tmp.get('goods_id'))

        pipeline.update_mia_xianshimiaosha_table(tmp)

    def get_url_body(self, tmp_url):
        '''
        根据url得到body
        :param tmp_url:
        :return: body   类型str
        '''
        # 设置代理ip
        self.proxies = self.get_proxy_ip_from_ip_pool()  # {'http': ['xx', 'yy', ...]}
        self.proxy = self.proxies['http'][randint(0, len(self.proxies) - 1)]

        tmp_proxies = {
            'http': self.proxy,
        }
        # print('------>>>| 正在使用代理ip: {} 进行爬取... |<<<------'.format(self.proxy))

        tmp_headers = self.headers
        tmp_headers['Host'] = re.compile(r'://(.*?)/').findall(tmp_url)[0]
        tmp_headers['Referer'] = 'https://' + tmp_headers['Host'] + '/'

        try:
            response = requests.get(tmp_url, headers=tmp_headers, proxies=tmp_proxies, timeout=12)  # 在requests里面传数据，在构造头时，注意在url外头的&xxx=也得先构造
            body = response.content.decode('utf-8')

            body = re.compile('\t').sub('', body)
            body = re.compile('  ').sub('', body)
            body = re.compile('\r\n').sub('', body)
            body = re.compile('\n').sub('', body)
            # print(body)
        except Exception:
            print('requests.get()请求超时....')
            print('data为空!')
            body = ''

        return body

    def get_proxy_ip_from_ip_pool(self):
        '''
        从代理ip池中获取到对应ip
        :return: dict类型 {'http': ['http://183.136.218.253:80', ...]}
        '''
        base_url = 'http://127.0.0.1:8000'
        result = requests.get(base_url).json()

        result_ip_list = {}
        result_ip_list['http'] = []
        for item in result:
            if item[2] > 7:
                tmp_url = 'http://' + str(item[0]) + ':' + str(item[1])
                result_ip_list['http'].append(tmp_url)
            else:
                delete_url = 'http://127.0.0.1:8000/delete?ip='
                delete_info = requests.get(delete_url + item[0])
        # pprint(result_ip_list)
        return result_ip_list

    def get_goods_id_from_url(self, mia_url):
        '''
        得到goods_id
        :param mia_url:
        :return: goods_id (类型str)
        '''
        is_mia_irl = re.compile(r'https://www.mia.com/item-.*?.html.*?').findall(mia_url)
        if is_mia_irl != []:
            if re.compile(r'https://www.mia.com/item-(\d+).html.*?').findall(mia_url) != []:
                tmp_mia_url = re.compile(r'https://www.mia.com/item-(\d+).html.*?').findall(mia_url)[0]
                if tmp_mia_url != '':
                    goods_id = tmp_mia_url
                else:   # 只是为了在pycharm运行时不跳到chrome，其实else完全可以不要的
                    mia_url = re.compile(r';').sub('', mia_url)
                    goods_id = re.compile(r'https://www.mia.com/item-(\d+).html.*?').findall(mia_url)[0]
                print('------>>>| 得到的卷皮商品的地址为:', goods_id)
                return goods_id
        else:
            print('蜜芽商品url错误, 非正规的url, 请参照格式(https://www.mia.com/item-)开头的...')
            return ''

    def __del__(self):
        gc.collect()

if __name__ == '__main__':
    mia = MiaParse()
    while True:
        mia_url = input('请输入待爬取的蜜芽商品地址: ')
        mia_url.strip('\n').strip(';')
        goods_id = mia.get_goods_id_from_url(mia_url)
        data = mia.get_goods_data(goods_id=goods_id)
        mia.deal_with_data()