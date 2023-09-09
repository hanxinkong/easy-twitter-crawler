"""
页面迭代器
"""
import json
from loguru import logger

from easy_twitter_crawler.twitter_crawler.exceptions import ArticleException, UserLoseException
from easy_twitter_crawler.twitter_crawler.twitter_types import *
from easy_twitter_crawler.twitter_crawler.constants import *
from easy_twitter_crawler.twitter_utils.twitter_utils import (
    quote, jsonpath, extract_cursor, find_element,
    for_to_regx_match, regx_match, generating_page_link
)


def iter_search_pages(key_word: str, request_fn: RequestFunction, **kwargs) -> Iterator[Page]:
    """
    搜索
    :return:
    """
    start_url = kwargs.pop('start_url', None)
    data_type = kwargs.pop('data_type', '')

    kwargs.update({'key_word': key_word, 'data_type': data_type})

    if not start_url:
        key_word = key_word
        start_url = SEARCH_URL.format(key_word=key_word, data_type=data_type, cursor='')
    return generic_iter_pages(start_url, PageParser, request_fn, **kwargs)


def iter_article_pages(article_id: str, request_fn: RequestFunction, **kwargs) -> Iterator[Page]:
    start_url = kwargs.pop('start_url', None)
    if not start_url:
        start_url = ARTICLE_API.format(article_id=article_id, cursor='')
        kwargs.update({'article_id': article_id})
    return generic_iter_pages(start_url, ArticlePageParser, request_fn, **kwargs)


def iter_user_pages(user_id: str, request_fn: RequestFunction, **kwargs) -> Iterator[Page]:
    start_url = kwargs.pop('start_url', None)
    if not start_url:
        start_url = USER_BASE_API.format(user_name=f'{user_id}')
    return generic_iter_pages(start_url, UserPageParser, request_fn, **kwargs)


def iter_comment_pages(article_id: str, request_fn: RequestFunction, **kwargs) -> Iterator[Page]:
    start_url = kwargs.pop('start_url', None)
    if not start_url:
        start_url = COMMENT_API.format(article_id=article_id, cursor='')
        kwargs.update({'article_id': article_id})
    return generic_iter_pages(start_url, ArticleCommentPageParser, request_fn, **kwargs)


def generic_iter_pages(start_url, page_parser_cls, request_fn, **kwargs) -> Iterator[Page]:
    next_url = start_url

    while next_url:
        try:
            response = request_fn(next_url, **kwargs)
        except Exception as e:
            response = None
            logger.error(f'error: {e}')
        parser = page_parser_cls(response)
        page = parser.get_pages(**kwargs)
        yield page
        next_page_info = parser.get_next_page(**kwargs)
        next_url = next_page_info.get('next_url')

        if next_url:
            logger.warning(f'request next url {next_url}')
        else:
            logger.warning('last page')
            return


class PageParser:
    """
    json数据清洗
    """
    article_ele_regex = r"^tweet-.*"
    promoted_article_ele_regex = r"^promoted-tweet.*"
    user_ele_regex = r"^user-.*"

    def __init__(self, response):
        self.response = response
        self.html = None
        self.json_data = None
        self._parse()
        self.data_length = 0
        self.last_cursor = ''

    def _parse(self):
        # jsons = []
        assert self.response is not None, 'response is null'
        self.json_data = json.loads(self.response.text)
        self.html = self.response.html

    def get_raw_page(self) -> RawPage:
        return self.html

    def get_next_page(self, **kwargs) -> Dict[str, Union[str, bool]]:
        assert self.json_data is not None, 'json_data is null'
        next_cursor = extract_cursor(self.json_data)

        key_word = kwargs.pop('key_word', '')
        data_type = kwargs.pop('data_type', '')

        next_url = None

        if next_cursor and self.last_cursor != next_cursor and self.data_length > 2:
            self.last_cursor = next_cursor
            next_url = generating_page_link(SEARCH_URL, key_word=key_word, data_type=data_type, cursor=next_cursor)

        return {'next_cursor': next_cursor, 'next_url': next_url}

    def get_pages(self, **kwargs) -> Page:
        assert self.json_data is not None, 'json_data is null'
        data_list = None

        data = jsonpath(
            self.json_data,
            [
                '$.data.search_by_raw_query.search_timeline.timeline.instructions[*].entries[*]',
                # 搜索-用户
                # '$.data.search_by_raw_query.search_timeline.timeline.instructions[*].entries[*].content.itemContent.user_results.result'
            ],
            first=False,
            default=[]
        )
        self.data_length = len(data)

        matches = jsonpath(data, '$..entryId', first=False, default=[])
        # 是否为用户类型
        user_type = False
        if len(matches) > 0:
            user_type = matches[0].startswith('user-')

        matched_values = [value for value in matches if
                          for_to_regx_match(
                              [self.article_ele_regex, self.promoted_article_ele_regex, self.user_ele_regex],
                              value,
                              first=True,
                              default=False
                          )]

        data = [find_element(data, i) for i in matched_values]

        if user_type:
            data = jsonpath(data, '$..content.itemContent.user_results.result', first=False, default=[])

        if not data_list:
            data_list = data

        assert data_list is not None
        return data_list


class VideoPageParser(PageParser):
    """
    视频json数据清洗
    """
    pass


class ArticlePageParser(PageParser):
    """
    文章json数据清洗
    """

    def get_pages(self, **kwargs) -> Page:
        assert self.json_data is not None, 'json_data is null'
        data_list = None
        article_id = kwargs.pop('article_id', '')

        data = jsonpath(
            self.json_data,
            [
                f"$..instructions[0].entries[?(@.entryId=='tweet-{article_id}')]",
                "$.data.tweetResult.result"
            ],
            first=True,
            default={}
        )

        if not data:
            raise ArticleException(article_id, '推文不存在')

        reason = jsonpath(data, '$..__typename', first=True, default='')
        if 'TweetUnavailable' in reason:
            raise ArticleException(article_id, '推文不可用,可能是受保护的')

        if not data_list:
            data_list = [data]
        assert data_list is not None
        return data_list

    def get_next_page(self, **kwargs) -> Dict[str, Union[str, bool]]:
        assert self.json_data is not None, 'json_data is null'

        return {'next_cursor': '', 'next_url': ''}


class UserPageParser(PageParser):
    """
    用户json数据清洗
    """

    def get_pages(self, **kwargs) -> Page:
        assert self.json_data is not None, 'json_data is null'

        data_list = None
        data = jsonpath(
            self.json_data,
            [
                '$.data.user.result',
            ],
            first=True,
            default={}
        )

        if not data:
            # 用户不存在
            user_id = jsonpath(kwargs, '$.options.user_id', first=True, default='')
            raise UserLoseException(user=user_id)

        if not data_list:
            data_list = [data]
        assert data_list is not None
        return data_list


class UserArticlePageParser(PageParser):
    """
    用户的文章json数据清洗
    """
    pass


class ArticleCommentPageParser(PageParser):
    """
    用户的文章评论json数据清洗
    """
    cmt_ele_regex = r'^conversationthread(?!.*showmore)'
    showmore_ele_regex = r'^cursor-showmorethreads-.*'

    def get_pages(self, **kwargs) -> Page:
        assert self.json_data is not None, 'json_data is null'
        data_list = None
        comment_elements = []

        article_id = kwargs.pop('article_id', '')

        data = jsonpath(
            self.json_data,
            '$..instructions[*].entries[*]',
            first=False,
            default=[]
        )

        # -----------------提取包含评论的节点---------------------#
        article_element = find_element(data, f'tweet-{article_id}', first=False, default={})

        if bool(jsonpath(
                article_element,
                '$..itemContent.tweet_results.result.legacy.in_reply_to_status_id_str',
                first=True,
                default=''
        )):
            comment_elements.extend(article_element)

        matches = jsonpath(data, '$..entryId', first=False, default=[])
        # 是否有显示更多评论
        show_more_matched = [value for value in matches if
                             regx_match(self.showmore_ele_regex, value, first=True, default=False)]

        matched_values = [value for value in matches if
                          regx_match(self.cmt_ele_regex, value, first=True, default=False)]

        data = [find_element(data, i) for i in matched_values]
        comment_elements.extend(jsonpath(
            data,
            '$.*.content.items[*]',
            first=False,
            default=[]
        ))
        # 二次处理无效数据
        matches = jsonpath(comment_elements, '$..entryId', first=False, default=[])
        matched_values = [value for value in matches if
                          regx_match(self.cmt_ele_regex, value, first=True, default=False)]

        comment_elements = [find_element(data, i) for i in matched_values]

        if not comment_elements and not show_more_matched:
            raise ArticleException(article_id, '回复不存在')

        if not data_list:
            data_list = comment_elements
        assert data_list is not None
        return data_list

    def get_next_page(self, **kwargs) -> Dict[str, Union[str, bool]]:
        assert self.json_data is not None, 'json_data is null'
        next_cursor = extract_cursor(self.json_data)

        article_id = kwargs.pop('article_id', '')

        next_url = None
        if next_cursor and self.last_cursor != next_cursor:
            self.last_cursor = next_cursor
            join_cursor = quote(JOIN_CURSOR.format(cursor=next_cursor))
            # print(next_cursor)
            next_url = generating_page_link(COMMENT_API, article_id=article_id, cursor=join_cursor)

        return {'next_cursor': next_cursor, 'next_url': next_url}
