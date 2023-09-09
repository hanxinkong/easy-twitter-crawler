from easy_twitter_crawler.twitter_utils import twitter_utils
from .twitter_filter import TwitterFilter


def get_proxy():
    return twitter_utils.get_proxy()


def get_headers(cookie: str):
    """获取头"""
    return twitter_utils.get_headers(cookie)
