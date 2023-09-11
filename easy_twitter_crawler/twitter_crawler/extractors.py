"""
推特清洗器
"""
import re

from easy_spider_tool import date_parse
from requests_html import HTML

from .exceptions import (ArticleLoginException, UserLoginException,
                         UserPrivateException, UserSuspendedException, UserException)
from .twitter_scraper import *
from .constants import *

from easy_twitter_crawler.twitter_utils.twitter_utils import (
    generating_page_link, jsonpath, regx_match,
    generating_page_links, quote,
    extract_error_info, extract_time
)


def extract_data(raw_html, options: Options, request_fn: RequestFunction, full_html=None) -> Union[
    Iterator[UserType],
    Iterator[ArticleType],
    Iterator[VideoType],
    Iterator[PhotoType],
    Iterator[CommentType]
]:
    return BaseExtractor(raw_html, options, request_fn, full_html).extract_data()


def extract_user(raw_html, options: Options, request_fn: RequestFunction, full_html=None) -> UserType:
    return UserExtractor(raw_html, options, request_fn, full_html).extract_data()


def extract_comment(raw_html, options: Options, request_fn: RequestFunction, full_html=None) -> CommentType:
    return CommentExtractor(raw_html, options, request_fn, full_html).extract_data()


def init_reaction():
    """
    互动量
    """
    return {
        'up_count': 0,  # 点赞量
        'cmt_count': 0,  # 评论量
        'read_count': 0,  # 阅读量
        'rtt_count': 0,  # 转发量
        'share_count': 0,  # 分享量
        'collect_count': 0,  # 收藏量
        'quote_count': 0,  # 引用量
        'play_count': 0  # 视频播放量
    }


class BaseExtractor:
    video_regex = re.compile(r'play_url\".*\"(http.*\.mp4\?.*=hw?)"')
    ele_regex = re.compile(r'<.*</.*>')

    def __init__(self, element, options, request_fn, full_html=None):
        self.element = element
        self.options = options
        self.request_fn = request_fn
        self._type = None
        self._content_html = None
        self.info = {}
        # 详情页
        self._detail_response = None

    @property
    def type(self):
        if self._type is not None:
            return self._type

        self._type = self.options.get('data_type', '')

        if any([
            self._type.capitalize() in (TOP, LATEST, VIDEOS, PHOTOS),
            self._type.lower() == REPLY,
            self._type.lower() == COMMENT
        ]):
            self._type = ARTICLE
        elif self._type.capitalize() == PEOPLE:
            self._type = USER

        return self._type.lower()

    def content_html(self, content=None):
        if self._content_html is not None:
            return self._content_html
        html = content if content else self.element.get('content', '')
        self._content_html = HTML(html=html)
        return self._content_html

    def detail_response(self):
        """
        详情页请求
        :param:
        :return:
        """
        if self._detail_response is not None:
            return self._detail_response
        self._detail_response = self.request_fn(self.info.get('source_url'))
        return self._detail_response

    def extract_data(self):
        """
        数据清洗入口
        :return:
        """
        # 推文/评论
        err_info = extract_error_info(self.element)
        msg = err_info['msg']

        article_id = self.extract_id()[f'{self.type}_id']

        if 'need to log in to Twitter' in msg:
            raise ArticleLoginException(article_id)
        elif '此推文不可用' in msg or 'This Tweet is unavailable' in msg:
            raise ArticleException(article_id, msg)
        elif '这条推文违反了 Twitter 规则' in msg:
            raise ArticleException(article_id, msg)

        # tweet_results = jsonpath(self.element, ['$...itemContent.tweet_results'], first=True, default={})
        # if not tweet_results:
        #     raise ArticleException(article_id, '推文不存在')

        methods = [
            self.extract_id,
            self.extract_pub_time,
            self.extract_author,
            self.extract_url,
            self.extract_pictures,
            self.extract_video_url,
            self.extract_play_duration,
            self.extract_init_reaction,
            self.extract_retweet,
            self.extract_quote,
            self.extract_embed_url,
            self.extract_language,
            self.extract_content,
        ]
        for method in methods:
            try:
                partial_info = method()
                if partial_info is None:
                    continue
                # logger.warning(f'method: {method.__name__} return: {partial_info}')
                self.info.update(partial_info)
            except Exception as ex:
                logger.debug(f'method: {method.__name__} error:{ex}')

        return self.info

    def extract_id(self) -> PartialType:
        # tweet-1671055903175372802
        data_id = ''  # jsonpath(self.options, '$.task_id', first=True, default='')
        if not data_id:
            data_id = jsonpath(
                self.element,
                [
                    "$..tweet_results.result.tweet.rest_id",
                    "$..itemContent.tweet_results.result.rest_id",
                    "$..entryId",
                    "$..rest_id"  # 新发文
                ],
                first=True,
                default=''
            )

        return {
            f'{self.type}_id': data_id.replace('tweet-', '')
        }

    def extract_pub_time(self) -> PartialType:
        """
        编辑时间
        :return:
        """
        pub_time = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result.legacy.created_at",
                "$..itemContent.tweet_results.result.tweet.legacy.created_at",
                "$..legacy.created_at"  # 新发文
            ],
            first=True,
            default=''
        )

        pub_time = extract_time(pub_time)

        return {
            'pub_time': pub_time
        }

    def extract_url(self) -> PartialType:
        """
        url 清洗
        """
        url = jsonpath(self.element, '$.url', first=True, default='')
        if not url:
            user_name = jsonpath(self.info, '$.author_info.user_name', first=True, default='')
            article_id = self.info.get(f'{self.type}_id', '')
            url = ARTICLE_URL.format(user_name=user_name, article_id=article_id) if all([user_name, article_id]) else ''

        return {
            'source_url': url
        }

    def extract_pictures(self) -> PartialType:
        """
        图片清洗
        """
        pic = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result.legacy.entities.media[*].media_url_https",
                "$..itemContent.tweet_results.result.tweet.legacy.entities.media[*].media_url_https",
                "$..legacy.entities.media[*].media_url_https"  # 新发文
            ],
            first=False,
            default=[]
        )
        pic = list(filter(lambda x: x and not "/video/" in x, pic))
        # pic = [i for i in pic if not "/video/" in i]
        return {
            'pictures': list(set(pic))
        }

    def extract_video_url(self) -> PartialType:
        """
        视频链接
        """
        video_url = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result.legacy.extended_entities.media[*].video_info.variants[?(@.content_type==\"video/mp4\")].url",
                "$..legacy.extended_entities.media[*].video_info.variants[?(@.content_type==\"video/mp4\")].url"
            ],
            first=False,
            default=[]
        )

        return {'video_url': list(set(video_url))}

    def extract_author(self, author_info=None) -> PartialType:
        """
        用户信息
        """
        user_id = jsonpath(
            self.element,
            [
                '$..itemContent.tweet_results.result..core.user_results.result.rest_id',
                '$..core.user_results.result.rest_id'  # 新发文
            ],
            first=True,
            default=''
        )
        user_name = jsonpath(
            self.element,
            [
                '$..itemContent.tweet_results.result..core.user_results.result.legacy.screen_name',
                '$..core.user_results.result.legacy.screen_name',  # 新发文
            ],
            first=True,
            default=''
        )

        user_url = USER_BASE_URL.format(user_name=user_name) if user_name else ''

        return {
            'author_info': {
                'user_id': user_id,
                'user_name': user_name,
                'user_url': user_url,
            }
        }

    def extract_init_reaction(self) -> PartialType:
        """
        统一解析互动量
        """

        init_ = init_reaction()
        init_.update({
            'up_count': jsonpath(
                self.element,
                [
                    '$..itemContent.tweet_results.result..legacy.favorite_count',
                    '$..legacy.favorite_count',  # 新发文
                ],
                first=True,
                default=0
            ),
            'cmt_count': jsonpath(
                self.element,
                [
                    '$..itemContent.tweet_results.result..legacy.reply_count',
                    '$..legacy.reply_count',  # 新发文
                ],
                first=True,
                default=0
            ),
            'read_count': int(jsonpath(
                self.element,
                [
                    '$..itemContent.tweet_results.result..views.count',
                    '$..views.count',
                ],
                first=True,
                default=0
            )),
            'rtt_count': jsonpath(
                self.element,
                [
                    '$..itemContent.tweet_results.result..legacy.retweet_count',
                    '$..legacy.retweet_count',
                ],
                first=True,
                default=0
            ),
            'share_count': 0,
            'collect_count': jsonpath(
                self.element,
                [
                    '$..legacy.bookmark_count',
                ],
                first=True,
                default=0
            ),
            'quote_count': jsonpath(
                self.element,
                [
                    '$..itemContent.tweet_results.result..legacy.quote_count',
                    '$..legacy.quote_count',
                ],
                first=True,
                default=0
            ),
            'play_count': jsonpath(
                self.element,
                [
                    '$..legacy.extended_entities.media[*].mediaStats.viewCount',
                ],
                first=True,
                default=0
            )
        })

        return init_

    def extract_play_duration(self) -> PartialType:
        """
        视频播放时长
        """
        play_duration = jsonpath(
            self.element,
            [
                '$..legacy.extended_entities.media[*].video_info.duration_millis',
            ],
            first=True,
            default=0
        )

        return {'play_duration': play_duration}

    def extract_retweet(self) -> PartialType:
        """
        转推信息
        """
        retweet_article_id = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result.legacy.retweeted_status_result.result.rest_id",
                "$..itemContent.tweet_results.result..legacy.retweeted_status_result.result.tweet.rest_id",
                "$..legacy.retweeted_status_result.result.rest_id",
            ],
            first=True,
            default=''
        )

        retweet_user_id = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result..legacy.retweeted_status_result.result.core.user_results.result.rest_id",
                "$..itemContent.tweet_results.result..tweet.legacy.retweeted_status_result.result.tweet.core.user_results.result.rest_id",
                "$..legacy.retweeted_status_result.result..core.user_results.result.rest_id",
            ],
            first=True,
            default=''
        )
        retweet_user_name = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result..legacy.retweeted_status_result.result.core.user_results.result.legacy.screen_name",
                "$..itemContent.tweet_results.result..tweet.legacy.retweeted_status_result.result.tweet.core.user_results.result.legacy.screen_name",
                "$..legacy.retweeted_status_result.result..core.user_results.result.legacy.screen_name",
            ],
            first=True,
            default=''
        )

        return {
            'is_retweet': bool(retweet_article_id),
            'retweet_info': {
                f'{self.type}_id': retweet_article_id,
                'retweet_author': {
                    'user_id': retweet_user_id,
                    'user_name': retweet_user_name,
                },
                'url': ARTICLE_URL.format(user_name=retweet_user_name, article_id=retweet_article_id) if all(
                    [retweet_article_id, retweet_user_name]) else ''
            }
        }

    def extract_quote(self) -> PartialType:
        """
        信息
        """
        quote_article_id = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result.quoted_status_result.result.rest_id",
                "$..itemContent.tweet_results.result..quoted_status_result.result.tweet.rest_id",
                "$..quoted_status_result.result.rest_id"
            ],
            first=True,
            default=''
        )

        quote_user_id = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result..quoted_status_result..user_results.result.rest_id",
                "$..quoted_status_result..user_results.result.rest_id",
            ],
            first=True,
            default=''
        )
        quote_user_name = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result..quoted_status_result..user_results.result.legacy.screen_name",
                "$..quoted_status_result..user_results.result.legacy.screen_name",
            ],
            first=True,
            default=''
        )

        return {
            'is_quote': bool(quote_article_id),
            'quote_info': {
                f'{self.type}_id': quote_article_id,
                'quote_author': {
                    'user_id': quote_user_id,
                    'user_name': quote_user_name,
                },
                'url': ARTICLE_URL.format(user_name=quote_user_name, article_id=quote_article_id) if all(
                    [quote_article_id, quote_user_name]) else ''
            }
        }

    def extract_embed_url(self) -> PartialType:
        """
        内嵌的url/本推文中提到的链接
        """
        short_links = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result..legacy.entities.urls[*].expanded_url",
                "$..itemContent.tweet_results.result..tweet.legacy.entities.urls[*].expanded_url",
                "$..legacy.entities.urls[*].expanded_url",
            ],
            first=False,
            default=[]
        )

        return {
            'embed_url': list(set(short_links))
        }

    def extract_language(self) -> PartialType:
        """
        语种
        """
        language = jsonpath(
            self.element,
            [
                "$..itemContent.tweet_results.result..legacy.lang",
                "$..itemContent.tweet_results.result..tweet.legacy.lang",
                "$..legacy.lang",
            ],
            first=True,
            default=''
        )

        return {
            'language': language
        }

    def extract_content(self, content=None) -> PartialType:
        content = jsonpath(self.element, '$.content', first=True) if content is None else content

        is_retweet = jsonpath(self.info, '$.is_retweet', first=True, default='')
        is_quote = jsonpath(self.info, '$.is_quote', first=True, default='')

        expr = [
            "$..itemContent.tweet_results.result..legacy.full_text",
            "$..itemContent.tweet_results.result..tweet.legacy.full_text",
            "$..legacy.full_text",
        ]

        if is_retweet:  # 转推完整文本
            expr = ["$..legacy.retweeted_status_result.result.legacy.full_text"]

        content = jsonpath(
            self.element,
            expr,
            first=True,
            default=''
        )

        if content and self.ele_regex.findall(content):
            contents = []
            for ele in self.content_html(content).find('p,h1,h2,h3,h4,h5,h6,pre>code,li'):
                if ele and ele.text:
                    if ele.text not in contents:
                        contents.append(ele.text)
            content = '\n'.join(contents)
            content = re.sub(r'<.*>', '', content)
        return {
            'content': content
        }

    def extract_meta_data(self, start_url, type_name, **kwargs) -> PartialType:
        """
        获取账号的文章,关注，粉丝数据
        :param start_url: 请求数据的接口
        :param type_name: 请求数据类型名称
        :return: 返回对应数据集合
        """
        pass


class UserExtractor(BaseExtractor):
    """
    用户信息
    """

    def extract_data(self):
        user_id = jsonpath(self.options, '$.user_id', first=True, default='')

        # 私密账号
        if jsonpath(self.element, '$..__typename', first=True, default='') == 'UserUnavailable':
            reason = jsonpath(self.element, '$..reason', first=True, default='')
            if reason.lower() in 'Suspended'.lower():
                raise UserSuspendedException(user_id)

            raise UserPrivateException(user_id)
        # 用户不存在
        if jsonpath(self.element, '$..data', first=True, default={}):
            raise UserLoseException(user_id)

        # 账户冻结
        err_info = extract_error_info(self.element)
        msg = err_info['msg']
        if '冻结违反' in msg or 'violate the Twitter Rules' in msg:
            raise UserException(user_id, '该用户被冻结')

        methods = [
            self.extract_user,
        ]
        for method in methods:
            try:
                partial_info = method()
                if partial_info is None:
                    continue
                # logger.warning(f'method: {method.__name__} return: {partial_info}')
                self.info.update(partial_info)
            except Exception as ex:
                logger.debug(f'method: {method.__name__} error:{ex}')

        # ********* 用户文章列表采集 ********* #
        total_count = self.info['tweets_count']
        count = self.options.get('article_count', -1)
        if count > -1 and total_count > 0:
            total_count = count if 0 < count < total_count else total_count
            cursor = ''
            start_url = generating_page_link(USER_ARTICLE_URL, cursor=cursor, user_id=self.info['user_id'])
            result = self.extract_meta_data(
                start_url=start_url,
                type_name=ARTICLE,
                total_count=total_count,
                user_id=self.info['user_id']
            ) or {}

            self.info.update(result)

        # ********* 用户回复列表采集 ********* #
        total_count = self.info['tweets_count']
        count = self.options.get('reply_count', -1)
        if count > -1 and total_count > 0:
            total_count = count if 0 < count < total_count else total_count
            cursor = ''
            start_url = generating_page_link(USER_REPLY_URL, cursor=cursor, user_id=self.info['user_id'])
            result = self.extract_meta_data(
                start_url=start_url,
                type_name=REPLY,
                total_count=total_count,
                user_id=self.info['user_id']
            ) or {}

            self.info.update(result)

        # ********* 用户粉丝列表采集 ********* #
        total_count = self.info['followers_count']
        count = self.options.get('followers_count', -1)
        if count > -1 and total_count > 0:
            total_count = count if 0 < count < total_count else total_count
            cursor = ''
            start_url = generating_page_link(USER_FOLLOWERS_API, cursor=cursor, user_id=self.info['user_id'])
            result = self.extract_meta_data(
                start_url=start_url,
                type_name=FOLLOWERS,
                total_count=total_count,
                user_id=self.info['user_id']
            ) or {}
            self.info.update(result)

        # ********* 用户关注列表采集 ********* #
        total_count = self.info['following_count']
        count = self.options.get('following_count', -1)
        if count > -1 and total_count > 0:
            total_count = count if 0 < count < total_count else total_count
            cursor = ''
            start_url = generating_page_link(USER_FOLLOWING_API, cursor=cursor, user_id=self.info['user_id'])
            result = self.extract_meta_data(
                start_url=start_url,
                type_name=FOLLOWING,
                total_count=total_count,
                user_id=self.info['user_id']
            ) or {}
            self.info.update(result)

        return self.info

    def extract_user(self) -> PartialType:

        birthday = jsonpath(self.element, ['$.legacy_extended_profile.birthdate'], first=True, default={})

        birthday_year = str(birthday.get('year', ''))
        birthday_month = str(birthday.get('month', ''))
        birthday_day = str(birthday.get('day', ''))

        user_name = jsonpath(self.element, ['$..screen_name'], first=True, default='')
        join_date = jsonpath(self.element, ['$..created_at'], first=True, default='')
        return {
            'user_id': jsonpath(self.element, ['$.rest_id', '$.id_str'], first=True, default=''),
            'user_name': user_name,
            'display_name': jsonpath(self.element, ['$..name'], first=True, default=''),
            'user_url': f'https://twitter.com/{user_name}' if user_name else '',
            'profile_picture': jsonpath(self.element, ['$..profile_image_url_https'], first=True, default=''),
            'header_photo': jsonpath(self.element, ['$..profile_banner_url'], first=True, default=''),
            'bio': jsonpath(self.element, ['$..description'], first=True, default=''),
            'location': jsonpath(self.element, ['$..location'], first=True, default=''),
            'website_link': {
                'display_url': jsonpath(self.element, ['$..entities.url.urls[*].display_url'], first=True,
                                        default=''),
                'expanded_url': jsonpath(self.element, ['$..entities.url.urls[*].expanded_url'], first=True,
                                         default=''),
            },
            'birthday': {
                'birthday': '-'.join([birthday_year, birthday_month, birthday_day]).strip('-'),
                'visibility': birthday.get('visibility', '')
            },
            'followers_count': jsonpath(self.element, ['$..followers_count'], first=True, default=0),
            'following_count': jsonpath(self.element, ['$..friends_count'], first=True, default=0),
            'tweets_count': jsonpath(self.element, ['$..statuses_count'], first=True, default=0),
            'likes_count': jsonpath(self.element, ['$..favourites_count'], first=True, default=0),
            'media_count': jsonpath(self.element, ['$..media_count'], first=True, default=0),
            'listed_count': jsonpath(self.element, ['$..listed_count'], first=True, default=0),
            'join_date': extract_time(join_date),
            'auth': {
                'is_verified': jsonpath(self.element, '$..verified', first=True, default=False),
                'verified_type': jsonpath(self.element, '$..verified_type', first=True, default=''),
                'verification_info': jsonpath(self.element, '$.verification_info.reason.description.text', first=True,
                                              default=''),
            },
            'professional': {
                'professional_category': jsonpath(self.element, '$.professional.category[*].name', first=True,
                                                  default=''),
                'professional_type': jsonpath(self.element, '$.professional.professional_type', first=True, default=''),
            },
            'protected': jsonpath(self.element, '$..protected', first=True, default=False),
        }

    def extract_meta_data(self, start_url, type_name, **kwargs) -> PartialType:
        """
        获取账号的文章,动态等数据
        :param start_url: 请求数据的接口
        :param type_name: 请求数据类型名称
        :return: 返回对应数据集合
        """
        total_count = kwargs.get('total_count', 0)
        user_id = kwargs.pop('user_id', False)
        start_time = self.options.pop('start_time', False)
        end_time = self.options.pop('end_time', False)

        if start_time:
            start_time = date_parse(start_time, default_time_scheme=None)

        if type_name == REPLY:
            self.options.update({'data_type': ARTICLE})
        else:
            self.options.update({'data_type': type_name})

        if total_count == 0:
            return

        page_urls = generating_page_links(start_url, total_count)
        data_list = []

        # ---------仅能一页一页采集------------#
        article_ele_regex = r"^tweet-.*"
        expr = []
        last_cursor = None
        next_cursor = ''
        join_cursor = None

        base_url = None

        if type_name in (FOLLOWERS, FOLLOWING):
            expr = [  # 用户粉丝/关注
                '$.data.user.result.timeline.timeline.instructions[-1:].entries[*].content.itemContent.user_results.result',
                '$.users[*]'  # 开发者api
            ]
            base_url = USER_FOLLOWERS_API if type_name == FOLLOWERS else USER_FOLLOWING_API
            join_cursor = USER_FOLLOWERS_CURSOR if type_name == FOLLOWERS else USER_FOLLOWING_CURSOR
        elif type_name == ARTICLE:
            expr = [  # 用户文章
                '$..entries[*]'
            ]
            base_url = USER_ARTICLE_URL
            join_cursor = USER_ARTICLE_CURSOR
        elif type_name == REPLY:
            expr = [  # 用户回复
                '$..instructions[*]..entries..items..item..tweet_results.result'
            ]
            base_url = USER_REPLY_URL
            join_cursor = USER_REPLY_CURSOR

        for page_url in page_urls:

            if next_cursor:
                next_cursor = quote(join_cursor.format(cursor=next_cursor))

            page_url = generating_page_link(base_url, cursor=next_cursor, user_id=user_id, data_type=type_name)

            logger.warning(f'request next url {page_url}')

            response = self.request_fn(page_url, **kwargs)

            # 翻页失败，停止继续翻页
            if response is None:
                break

            if response and response.status_code == 200:
                response_json = json.loads(response.text) if response else {}

                err_info = extract_error_info(response_json)

                # 需要登录
                if err_info['name'] == 'AuthorizationError':
                    raise UserLoginException(user_id)

                elements = jsonpath(
                    response_json,
                    expr,
                    first=False,
                    default=[]
                )

                # 后续没有文章了
                if len(elements) < 3:
                    break

                for element in elements:
                    if total_count <= len(data_list):
                        return {
                            type_name: data_list
                        }

                    if type_name == FOLLOWERS:
                        extractor = UserFriendExtractor(element, self.options, self.request_fn, full_html=None)
                    elif type_name == FOLLOWING:
                        extractor = UserFollowingExtractor(element, self.options, self.request_fn, full_html=None)
                    elif type_name == ARTICLE:
                        # 置顶推文
                        # 排除推荐
                        entry_id = jsonpath(element, ['$..entryId'], first=True, default='')
                        if not regx_match(article_ele_regex, entry_id, first=True, default=False):
                            continue
                        extractor = BaseExtractor(element, self.options, self.request_fn, full_html=None)
                    elif type_name == REPLY:
                        # 排除文章，只要回复
                        reply_type = jsonpath(element, ['$..in_reply_to_status_id_str'], first=True, default='')
                        if not reply_type:
                            continue
                        extractor = UserReplyExtractor(element, self.options, self.request_fn, full_html=None)
                    else:
                        extractor = BaseExtractor(element, self.options, self.request_fn, full_html=None)

                    result = extractor.extract_data()
                    # yield result
                    pub_time = result.get('pub_time', '')
                    # 根据时间过滤
                    if start_time and pub_time <= start_time:
                        return {
                            type_name: data_list
                        }
                    if end_time and pub_time >= end_time:
                        continue

                    data_list.append(result)

                next_cursor = extract_cursor(response_json)

                if type_name == ARTICLE or type_name == REPLY:
                    if next_cursor == '' or last_cursor == next_cursor:
                        break
                elif type_name in (FOLLOWERS, FOLLOWING):
                    if str(next_cursor) == str(0) or last_cursor == next_cursor:
                        break
                # elif type_name == FOLLOWERS:
                # node_type = jsonpath(response_json,
                #                      '$.data.user.result.timeline.timeline.instructions[*].entries..element',
                #                      first=True, default='')
                # if next_cursor == '' or node_type != 'user':
                #     break

                last_cursor = next_cursor

        return {type_name: data_list}


class UserArticleExtractor(UserExtractor):
    """
    用户文章
    """
    pass


class UserReplyExtractor(BaseExtractor):
    """
    用户回复
    """

    def __init__(self, element, options, request_fn, full_html=None):
        super().__init__(element, options, request_fn)

    def extract_data(self):
        """
        数据清洗入口
        :return:
        """

        self.info.update(**super().extract_data())
        methods = [
            self.extract_ref_article_id,
            self.extract_ref_author,
        ]

        for method in methods:
            try:
                partial_info = method()
                if partial_info is None:
                    continue
                # logger.warning(f'method: {method.__name__} return: {partial_info}')
                self.info.update(partial_info)
            except Exception as ex:
                logger.debug(f'method: {method.__name__} error:{ex}')

        return self.info

    def extract_ref_article_id(self) -> PartialType:
        """
        被评论文章id
        @return:
        """
        article_id = jsonpath(self.element, ['$..in_reply_to_status_id_str'], first=True, default='')

        return {'ref_article_id': article_id}

    def extract_ref_author(self) -> PartialType:
        """
        被评论文章id
        @return:
        """
        user_id = jsonpath(self.element, ['$..in_reply_to_user_id_str'], first=True, default='')
        user_name = jsonpath(self.element, ['$..in_reply_to_screen_name'], first=True, default='')

        user_url = USER_BASE_URL.format(user_name=user_name) if user_name else ''
        return {
            'ref_author_info': {
                'user_id': user_id,
                'user_name': user_name,
                'user_url': user_url,
            }
        }


class UserFriendExtractor(UserExtractor):
    """
    用户关注人或粉丝
    """

    def extract_data(self):
        return self.extract_user()


class UserFollowingExtractor(UserExtractor):
    """
    用户关注
    """

    def extract_data(self):
        return self.extract_user()


class CommentExtractor(BaseExtractor):
    """
    发文评论
    """

    def __init__(self, element, options, request_fn, full_html=None):
        super().__init__(element, options, request_fn)

    def extract_data(self):
        """
        数据清洗入口
        :return:
        """

        self.info.update(**super().extract_data())
        methods = [
            self.extract_ref_article_id,
            self.extract_ref_author,
            self.extract_ref_source_url,
            self.extract_root_article_id,
            self.extract_root_author,
            self.extract_root_source_url,
        ]

        for method in methods:
            try:
                partial_info = method()
                if partial_info is None:
                    continue
                # logger.warning(f'method: {method.__name__} return: {partial_info}')
                self.info.update(partial_info)
            except Exception as ex:
                logger.debug(f'method: {method.__name__} error:{ex}')

        return self.info

    def extract_ref_article_id(self) -> PartialType:
        """
        被评论文章id
        @return:
        """
        article_id = jsonpath(self.element, ['$..in_reply_to_status_id_str'], first=True, default='')

        return {'ref_article_id': article_id}

    def extract_ref_author(self) -> PartialType:
        """
        被评论文章作者信息
        @return:
        """
        user_id = jsonpath(self.element, ['$..in_reply_to_user_id_str'], first=True, default='')
        user_name = jsonpath(self.element, ['$..in_reply_to_screen_name'], first=True, default='')

        user_url = USER_BASE_URL.format(user_name=user_name) if user_name else ''
        return {
            'ref_author_info': {
                'user_id': user_id,
                'user_name': user_name,
                'user_url': user_url,
            }
        }

    def extract_ref_source_url(self) -> PartialType:
        """
        被评论文章url
        @return:
        """
        user_name = jsonpath(self.info, '$.ref_author_info.user_name', first=True, default='')
        article_id = jsonpath(self.info, '$.ref_article_id', first=True, default='')
        url = ARTICLE_URL.format(user_name=user_name, article_id=article_id) if all([user_name, article_id]) else ''

        return {'ref_source_url': url}

    def extract_root_article_id(self) -> PartialType:
        """
        根文章id
        @return:
        """
        article_id = jsonpath(self.element, ['$..conversation_id_str'], first=True, default='')

        return {'root_article_id': article_id}

    def extract_root_author(self) -> PartialType:
        """
        根文章用户信息
        @return:
        """
        user_id = jsonpath(self.element, ['$..entities.user_mentions[-1:].id_str'], first=True, default='')
        user_name = jsonpath(self.element, ['$..entities.user_mentions[-1:].screen_name'], first=True, default='')
        user_url = USER_BASE_URL.format(user_name=user_name) if user_name else ''

        return {
            'root_author_info': {
                'user_id': user_id,
                'user_name': user_name,
                'user_url': user_url,
            }
        }

    def extract_root_source_url(self) -> PartialType:
        """
        根文章url
        @return:
        """
        user_name = jsonpath(self.info, '$.root_author_info.user_name', first=True, default='')
        article_id = jsonpath(self.info, '$.root_article_id', first=True, default='')
        url = ARTICLE_URL.format(user_name=user_name, article_id=article_id) if all([user_name, article_id]) else ''

        return {'root_source_url': url}
