""""
推特工具类
"""
import datetime
import re
import requests
import time
import urllib3
from loguru import logger
from math import ceil
from my_fake_useragent import UserAgent
from urllib.parse import unquote, urljoin, quote
from easy_spider_tool import jsonpath, cookie_to_dic, clear_value, regx_match, for_to_regx_match, date_parse
from requests import RequestException

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from easy_twitter_crawler.twitter_crawler.twitter_types import *

bearer = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'


def get_proxy():
    """
    获取代理
    """
    proxy_meta = {
        'http': 'http://127.0.0.1:10808',
        'https': 'http://127.0.0.1:10808'
    }
    return proxy_meta


def get_headers(cookie: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68',
        'content-type': 'application/json',
        'x-twitter-active-user': 'yes',
        # 'x-twitter-auth-type': 'OAuth2Session',
        'authorization': bearer,
    }

    # 无需登录
    if not cookie:
        headers.update({
            'x-guest-token': gen_guest_token()
        })
    else:
        headers.update({
            'x-csrf-token': cookie_to_dic(cookie)['ct0'],
            'cookie': cookie,
        })
    return headers


def extract_time(date_obj: str) -> str:
    """
    时间处理
    """
    if not date_obj:
        return ''

    date_obj = (date_parse(
        date_obj.replace('+0000', ''),
        is_fmt=False,
        default_time_scheme=None,
        # timezone='Asia/Shanghai'
    ) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

    return date_obj


def extract_error_info(json_data: Dict) -> PartialType:
    """
    处理错误消息
    @param json_data:
    @return:
    """

    return {
        'msg': jsonpath(
            json_data,
            [
                '$.errors..message',
                # 推文不可用/推文需要登录
                '$..itemContent.tweet_results.result.tombstone..text.text',
                '$..text.text',
                # 用户报错信息
                '$.data.user.result..text',
            ],
            first=True,
            default=''
        ),
        'name': jsonpath(
            json_data,
            '$.errors..name',
            first=True,
            default=''
        ),
        'type': jsonpath(
            json_data,
            '$.errors..kind',
            first=True,
            default=''
        ),
        'code': jsonpath(
            json_data,
            '$.errors..code',
            first=True,
            default=''
        ),
    }


def extract_cursor(json_data: Dict) -> str:
    """
    处理翻页cursor
    @param json_data:
    @return:
    """
    expr = [
        # 文章评论
        "$.data..instructions[0].entries.[?(@.cursorType=='Bottom'||@.cursorType=='ShowMoreThreads'||@.cursorType=='ShowMoreThreadsPrompt')].value",
        # 用户粉丝/关注
        "$.data.user.result.timeline.timeline.instructions[*].entries.[?(@.cursorType=='Bottom')].value",
        # 用户文章
        "$..entries.[?(@.cursorType=='Bottom')].value",
        # 搜索
        "$.data.search_by_raw_query.search_timeline.timeline.instructions..[?(@.cursorType=='Bottom')].value"
    ]

    cursor = jsonpath(
        json_data,
        expr,
        first=True,
        default=''
    )
    return cursor


def generating_page_link(base_url: str, cursor: str = None, **kwargs) -> Optional[str]:
    """
    根据cursor生成链接
    """
    page_url = None
    article_id = kwargs.pop('article_id', False)
    user_id = kwargs.pop('user_id', False)
    key_word = kwargs.pop('key_word', False)
    data_type = kwargs.pop('data_type', False)

    # 文章页
    if article_id:
        page_url = base_url.format(article_id=article_id, cursor=cursor)

    # 用户页
    if user_id:
        page_url = base_url.format(user_id=user_id, cursor=cursor)
    # 粉丝
    if data_type in ('followers', 'following'):
        if user_id and cursor:
            page_url = base_url.format(user_id=user_id) + f'&cursor={cursor}'

    # 搜索页
    if key_word:
        data_type = kwargs.pop('data_type', '')
        page_url = base_url.format(key_word=key_word, data_type=data_type, cursor=cursor)

    return page_url


def generating_page_links(base_url, total_num=50, limit=20):
    """
    根据总数及每页显示的个数生成下一页的urls
    @param base_url: 基础的url
    @param total_num: 数据总数 默认50
    @param limit: 每页展示的个数 默认20
    """
    page_urls = []
    for i in range(ceil(total_num / limit)):
        page_urls.append(re.sub(rf'start=\d+&count=\d+', f'start={i * limit}&count={limit}', base_url))
    return page_urls


def find_element(element, entity_id: str, key: str = 'entryId', first=True, default=None) -> Union[
    List[Dict[str, any]], Dict[str, any]]:
    if default is None:
        default = '' if first is True else []
    return jsonpath(element, f'$.[?(@["{key}"]=="{entity_id}")]', first=first, default=default)


def get_useragent():
    """
    随机获取useragent
    Returns: useragent
    """
    return UserAgent(phone=False, family='chrome', os_family='windows').random()


def gen_guest_token():
    """获取guest_token参数"""
    url_base = f'https://api.twitter.com/1.1/guest/activate.json'
    headers_ua = {
        'authorization': bearer,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }
    response = request('post', url_base, headers=headers_ua, proxies=get_proxy())
    if response is None:
        return
    res_json = response.json()
    guest_token = res_json.get('guest_token')
    return guest_token


class MaxRequestRetryCount(Exception):
    pass


def request(method: str, url: str, headers: Dict[str, str] = None, retry_num: int = 3, **kwargs) -> Response:
    retry_count = 0
    while retry_num >= retry_count:
        try:
            return requests.request(method.lower(), url, headers=headers, verify=False, **kwargs)

        except RequestException as rex:
            logger.error(
                f'request exception: {rex}' + f', kwargs: {kwargs}, next retry ...' if retry_count < retry_num else 'exit retry')
            retry_count += 1

    raise MaxRequestRetryCount(f'retry count: {retry_count}')
