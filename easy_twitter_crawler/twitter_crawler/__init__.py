from .twitter_types import *
from .twitter_scraper import TwitterScraper
from .constants import *

_scraper = TwitterScraper()


def set_cookie(cookie=None):
    """
    :param cookie: cookie 字典；格式为{'d_c0': '.....'}；
    """
    if cookie is None:
        cookie = {}

    cookies = []
    for key in cookie.keys():
        value = cookie[key]
        cookie_str = f'{key}={value}'
        cookies.append(cookie_str)
    _scraper.default_headers['cookie'] = '; '.join(cookies)


def set_proxy(proxy: Optional[Dict[str, str]] = None):
    """
    设置代理；每次请求都切换一次代理才算最佳
    """
    _scraper.set_proxy(proxy)


def _set_timeout(timeout: int):
    assert isinstance(timeout, int), 'timeout值应为大于0的整数'
    if timeout < 5 or timeout < 0:
        timeout = DEFAULT_REQUESTS_TIMEOUT
    _scraper.set_timeout(timeout=timeout)


def search_crawler(key_word: Optional[str] = None,
                   count: Optional[int] = 0,
                   comment_count: Optional[int] = -1,
                   **kwargs) -> Union[Iterator[UserType],
Iterator[ArticleType],
Iterator[VideoType],
Iterator[PhotoType]]:
    """
    关键词搜索采集（...）
    :param key_word: 关键词
    :param kwargs:
    :param count: (int) 采集指定数量的。该值过大可能会导致多次请求。-1 不采集 0采集全部（默认） >0采集指定的数量
    :param comment_count: (int) 采集指定数量的评论。该值过大可能会导致多次请求。默认-1 不采集 0采集全部 >0采集指定的数量
    @ page_limit (int): 需要采集的页数, 默认为constants下的 DEFAULT_PAGE_LIMIT
    @ data_type:（str or list or set or tuple） 获取数据类型 可选择（热门：Top 用户：People 最新：Latest 视频：Videos 照片：Photos） 大小写均可，默认所有类型都会采集
    @ drill_down_count: (int) 下钻内容采集数量(问题下的回答)，，默认-1 不采集 0采集全部 >0采集指定的数量
    :return:
    """
    _set_timeout(kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT))
    _scraper.requests_kwargs['timeout'] = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
    options: Union[Dict[str, Any], Set[str]] = kwargs.setdefault('options', {})
    if isinstance(options, set):
        options = {k: True for k in options}
    options.setdefault('key_word', key_word)
    options['drill_down_count'] = kwargs.pop('drill_down_count', -1)
    options['comment_count'] = comment_count
    data_types = kwargs.get('data_type', ALL_SEARCH_TYPE)
    kwargs['data_type'] = options['data_type'] = data_types
    kwargs['sort'] = options['sort'] = kwargs.get('sort', None)
    kwargs['time_interval'] = options['time_interval'] = kwargs.get('time_interval', None)
    kwargs['total_count'] = count

    data_types = [data_types] if isinstance(data_types, str) else data_types
    if isinstance(data_types, list):
        for data_type in data_types:
            kwargs['data_type'] = data_type.capitalize()
            for result in _scraper.search_crawler(key_word, **kwargs):
                yield result


def common_crawler(task_id: Union[str],
                   data_type: Optional[str] = None,
                   drill_down_count: Optional[int] = -1,
                   comment_count: Optional[int] = -1,
                   **kwargs) -> Union[Iterator[CommentType],
Iterator[ArticleType]]:
    """
    通用采集()
    :param task_id:
    :param data_type: 指定数据类型的采集 (article or comment)
    :param drill_down_count: (int) 下钻内容采集数量 (文章可下钻采集评论)，默认-1 不采集 0采集全部 >0采集指定的数量
    :param comment_count: (int) 采集指定数量的评论。该值过大可能会导致多次请求;默认-1 不采集 0采集全部 >0采集指定的数量
    :return:
    """
    _set_timeout(kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT))
    options: Union[Dict[str, Any], Set[str]] = kwargs.setdefault('options', {})
    if isinstance(options, set):
        options = {k: True for k in options}
    if data_type:
        options['data_type'] = data_type
    kwargs['pubdate_sort'] = kwargs.get('pubdate_sort', True)
    options['drill_down_count'] = kwargs['drill_down_count'] = drill_down_count
    options['comment_count'] = comment_count
    options['task_id'] = task_id
    options['start_time'] = kwargs.get('start_time', '')
    options['end_time'] = kwargs.get('end_time', '')
    kwargs['total_count'] = comment_count

    assert data_type in (ARTICLE, COMMENT), '匹配不到可以采集的数据类型，请校对data_type的值'

    if data_type == ARTICLE:
        return _scraper.article_crawler(article_id=task_id, **kwargs)
    elif data_type == COMMENT:
        return _scraper.comment_crawler(article_id=task_id, **kwargs)


def user_crawler(user_id: Union[str],
                 **kwargs) -> Iterator[UserType]:
    """
    账号采集
    :param user_id: (str) 账号id 如 https://twitter.com/phivolcs_dost中 phivolcs_dost中为user_id
                    数据api：

    @ followers_count： 是否采集该账号的关注列表(粉丝) -1不采集 默认。0采集全部（可能会导致多次请求）；>0将采集指定数量
    @ following_count： 是否采集该账号的好友列表（关注别人） -1不采集 默认。0采集全部（可能会导致多次请求）；>0将采集指定数量
    @ article_count： 是否采集该账号的文章列表 -1不采集 默认。0采集全部（可能会导致多次请求）；>0将采集指定数量
    @ drill_down_count: 是否向下钻取内容（）-1不采集 默认。0采集全部（可能会导致多次请求）；>0将采集指定数量
    """
    _set_timeout(kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT))
    options: Union[Dict[str, Any], Set[str]] = kwargs.setdefault('options', {})
    if isinstance(options, set):
        options = {k: True for k in options}
    options['followers_count'] = kwargs.pop('followers_count', -1)
    options['following_count'] = kwargs.pop('following_count', -1)
    options['article_count'] = kwargs.pop('article_count', -1)
    options['reply_count'] = kwargs.pop('reply_count', -1)
    options['drill_down_count'] = kwargs.pop('drill_down_count', -1)
    kwargs['sort'] = options['sort'] = kwargs.get('sort', 'created')
    options['user_id'] = user_id
    options['start_time'] = kwargs.get('start_time', '')
    options['end_time'] = kwargs.get('end_time', '')

    return _scraper.user_crawler(user_id, **kwargs)
