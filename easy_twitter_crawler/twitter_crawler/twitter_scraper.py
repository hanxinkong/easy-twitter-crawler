import time
import itertools
import asyncio
from requests_html import HTMLSession, AsyncHTMLSession
from functools import partial
from easy_twitter_crawler.twitter_utils.twitter_utils import get_useragent, get_headers
from .page_iterators import *
from .constants import *
from .twitter_types import *
from .extractors import extract_data, extract_user, extract_comment


class TwitterScraper:
    """
    推特采集
    """
    default_headers = {
        "user-agent": get_useragent(),
    }

    def __init__(self, session=None, async_session=None, requests_kwargs=None):
        if session is None:
            session = HTMLSession()
            session.headers.update(self.default_headers)
        if requests_kwargs is None:
            requests_kwargs = {}
        if async_session is None:
            async_session = AsyncHTMLSession(workers=ASYNC_COUNT)
            async_session.headers.update(self.default_headers)
        self.async_session = async_session
        self.session = session
        self.requests_kwargs = requests_kwargs

    def set_proxy(self, proxy: Optional[Dict[str, str]] = None):
        """
        设置代理
        :param proxy: proxy = {'http': 'http://ip:port', 'https': 'http://ip:port'}
        :return:
        """
        proxies = {
            'proxies': proxy
        }
        self.requests_kwargs.update(proxies)

    def set_timeout(self, timeout: int):
        """
        设置请求超时 单位秒
        """
        self.requests_kwargs['timeout'] = timeout

    def search_crawler(self, key_word: Union[str], **kwargs) -> Union[Iterator[UserType],
    Iterator[ArticleType],
    Iterator[VideoType],
    Iterator[PhotoType]]:
        """
        通过关键词对检索结果进行采集
        :param key_word: 需要采集的关键词
        :return:
        """
        kwargs['scraper'] = self
        iter_search_pages_fn = partial(iter_search_pages, key_word=key_word, request_fn=self.send, **kwargs)
        data_type = kwargs.get('data_type', '')

        if data_type == PEOPLE:
            extractor = extract_user
        else:
            extractor = extract_data

        return self._generic_crawler(extractor, iter_search_pages_fn, **kwargs)

    def article_crawler(self, article_id: Union[str], **kwargs) -> Iterator[ArticleType]:
        """
        通过文章id采集文章页数据
        """
        kwargs['scraper'] = self
        iter_article_pages_fn = partial(iter_article_pages, article_id=article_id, request_fn=self.send, **kwargs)
        return self._generic_crawler(extract_data, iter_article_pages_fn, **kwargs)

    def user_crawler(self, user_id: Union[str], **kwargs) -> Iterator[UserType]:
        """
        通过账号id采集个人主页数据
        """
        kwargs['scraper'] = self
        iter_user_page_fn = partial(iter_user_pages, user_id=user_id, request_fn=self.send, **kwargs)
        return self._generic_crawler(extract_user, iter_user_page_fn, **kwargs)

    def comment_crawler(self, article_id: Union[str], **kwargs) -> Iterator[UserType]:
        """
        通过文章id采集文章页评论
        """
        kwargs['scraper'] = self
        iter_comment_page_fn = partial(iter_comment_pages, article_id=article_id, request_fn=self.send, **kwargs)
        return self._generic_crawler(extract_comment, iter_comment_page_fn, **kwargs)

    def send(self, url, **kwargs):
        if not url:
            logger.error('url is null')
        method = kwargs.get('method', 'GET')
        return self.post(url, **kwargs) if method == 'POST' else self.get(url, **kwargs)

    def get(self, url, **kwargs):
        """
        请求方法
        """
        assert url is not None, 'url is null'
        if isinstance(url, str):
            cookie = self.default_headers.get('cookie')
            self.default_headers.update(get_headers(cookie) or {})
            self.session.headers.update(self.default_headers)

            retry_limit = 5
            response = None
            for retry in range(1, retry_limit + 1):
                try:
                    time.sleep(DEFAULT_REQUESTS_SLEEP)
                    response = self.session.get(url, **self.requests_kwargs)
                    response.raise_for_status()
                    return response
                except Exception as e:
                    if retry < retry_limit:
                        sleep_time = retry * 3
                        logger.debug(f'重连第{retry}次，休眠{sleep_time}秒, 异常：{e}')
                        time.sleep(sleep_time)

            assert response is not None, f'重新请求{retry_limit}次， response为空'

        if isinstance(url, list):  # 使用协程请求
            return self.generic_response(url, **kwargs)

    def generic_response(self, urls, **kwargs):
        urls = [urls[i: i + ASYNC_COUNT] for i in range(0, len(urls), ASYNC_COUNT)]
        for sub_urls in urls:
            tasks = [lambda url=url: self.async_get(url, **kwargs) for url in sub_urls]
            results = self.async_session.run(*tasks)
            yield results

    async def async_get(self, url, **kwargs):
        if self.default_headers.get('cookie', False):
            self.default_headers.update(get_headers(self.default_headers.get('cookie')) or {})
        self.async_session.headers.update(self.default_headers)
        try:
            response = await self.async_session.get(url, **self.requests_kwargs)
            if response and response.status_code != 200:
                logger.error(f'request url: {url}, response code: {response.status_code}')
            await asyncio.sleep(2)
            return response
        except Exception as e:
            logger.error(f'error: {e}')

    def post(self, url, **kwargs):
        pass

    def _generic_crawler(self,
                         extract_fn,
                         iter_pages_fn,
                         options=None,
                         **kwargs):
        """
        中转函数
        @extract_fn 数据清洗方法
        @iter_pages_fn 页面处理方法
        @options 参数
        """
        page_limit = kwargs.get('page_limit') if kwargs.get('page_limit', 0) else DEFAULT_PAGE_LIMIT
        counter = itertools.count(0) if page_limit is None else range(page_limit)
        if options is None:
            options = {}
        elif isinstance(options, set):
            options = {k: True for k in options}
        total_count = kwargs.get('total_count', 0)
        count = 0

        for i, page in zip(counter, iter_pages_fn()):
            for element in page:
                if 0 < total_count <= count:
                    return None

                count += 1
                try:
                    info = extract_fn(element, options=options, request_fn=self.send)
                    yield info
                except Exception as e:
                    raise
                    # logger.error(e)
