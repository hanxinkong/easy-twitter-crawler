# from gevent import monkey
# monkey.patch_all()
from easy_spider_tool import cookie_to_dic, format_json
from easy_twitter_crawler import set_proxy, set_cookie, common_crawler, user_crawler, search_crawler, TwitterFilter

proxy = {
    'http': 'http://127.0.0.1:10808',
    'https': 'http://127.0.0.1:10808'
}
# cookie = 'auth_token=686fa28f49400698820d0a3c344c51e3e44af73a; ct0=5bed99b7faad9dcc742eda564ddbcf37777f8794abd6d4d736919234440be2172da1e9a9fc48bb068db1951d1748ba5467db2bc3e768f122794265da0a9fa6135b4ef40763e7fd91f730d0bb1298136b'
cookie = ''
set_proxy(proxy)
set_cookie(cookie_to_dic(cookie))
num = 0

# 关键词采集使用案例（对关键词指定条件采集10条数据）
# key_word = 'elonmusk'
#
# twitter_filter = TwitterFilter(key_word)
# twitter_filter.word_category(lang='zh')
# twitter_filter.account_category(filter_from=None, to=None, at=None)
# twitter_filter.filter_category(only_replies=None, only_links=None, exclude_replies=None, exclude_links=None)
# twitter_filter.interact_category(min_replies=None, min_faves=None, min_retweets=None)
# twitter_filter.date_category(since='', until='')
# key_word = twitter_filter.filter_join()
#
# print(key_word)

# for info in search_crawler(
#         key_word,
#         data_type='Top',
#         count=10,
# ):
#     set_proxy(proxy)
#     set_cookie(cookie_to_dic(cookie))
#     num += 1
#     print(format_json(info))

# 用户信息采集使用案例（采集该用户信息及10条文章，10条回复，10个粉丝信息，10个关注信息）
for info in user_crawler(
        'elonmusk',
        article_count=10,
        reply_count=10,
        following_count=10,
        followers_count=10,
        # start_time='2023-07-20 00:00:00',
        # end_time='2023-07-27 00:00:00',
):
    set_proxy(proxy)
    set_cookie(cookie_to_dic(cookie))
    num += 1
    print(format_json(info))
    print(f"文章数：{len(info.get('article', []))}")
    print(f"粉丝数：{len(info.get('followers', []))}")
    print(f"关注数：{len(info.get('following', []))}")
    print(f"回复数：{len(info.get('reply', []))}")

# 通用采集使用案例（已知文章id，采集此文章信息）
# for info in common_crawler(
#         '1684447438864785409',
#         data_type='article',
#         # comment_count=1
# ):
#     set_proxy(proxy)
#     set_cookie(cookie_to_dic(cookie))
#     num += 1
#     print(format_json(info))
#
# print(num)
