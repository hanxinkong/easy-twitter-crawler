# 元搜索

## search_crawler

关键词采集

### 参数

| 字段名    | 类型   | 必须 | 描述                                                         |
| --------- | ------ | ---- | ------------------------------------------------------------ |
| key_word  | string | 是   | 关键词                                                       |
| data_type | string | 否   | 指定采集的板块，大小写均可（热门：Top 用户：People 最新：Latest 视频：Videos 照片：Photos） |
| count     | int    | 否   | 采集的数量（默认不采集：-1，采集全部：0，采集指定的数量：>0） |

关键词过滤参数说明（对标推特搜索功能，同一参数多个值间用空格隔开）

| 所属类别              | 字段名             | 类型     | 必须 | 描述                       |
|-------------------|-----------------|--------|----|--------------------------|
| word_category     | exact           | string | 否  | 精确短语                     |
| word_category     | filter_any      | string | 否  | 任何一词（支持多个)               |
| word_category     | exclude         | string | 否  | 排除这些词语 (支持多个) 示例：dog cat |
| word_category     | tab             | string | 否  | 这些话题标签（支持多个)             |
| word_category     | lang            | string | 否  | 语言（文档后附语言可选范围）           |   
| account_category  | filter_from     | string | 否  | 来自这些账号（支持多个)             |
| account_category  | to              | string | 否  | 发给这些账号（支持多个)             |
| account_category  | at              | string | 否  | 提及这些账号（支持多个)             |
| filter_category   | only_replies    | bool   | 否  | 仅回复                      |
| filter_category   | only_links      | bool   | 否  | 仅链接                      |
| filter_category   | exclude_replies | bool   | 否  | 排除回复                     |
| filter_category   | exclude_links   | bool   | 否  | 排除链接                     |
| interact_category | min_replies     | int    | 否  | 最少回复次数                   |
| interact_category | min_faves       | int    | 否  | 最少喜欢次数                   |
| interact_category | min_retweets    | int    | 否  | 最少转推次数                   |
| date_category     | since           | string | 否  | 开始日期（'2023-07-20'）       |
| date_category     | until           | string | 否  | 结束日期（'2023-08-20'）       |

### 示例（对关键词指定条件采集10条数据）

```python
from easy_spider_tool import cookie_to_dic, format_json
from easy_twitter_crawler import set_proxy, set_cookie, search_crawler, TwitterFilter

key_word = 'elonmusk'

twitter_filter = TwitterFilter(key_word)
twitter_filter.word_category(lang='en')
twitter_filter.account_category(filter_from='', to='', at='')
twitter_filter.filter_category(only_replies=None, only_links=None, exclude_replies=None, exclude_links=None)
twitter_filter.interact_category(min_replies='', min_faves='', min_retweets='')
twitter_filter.date_category(since='', until='')
key_word = twitter_filter.filter_join()

set_proxy(proxy)
set_cookie(cookie_to_dic(cookie))

for info in search_crawler(
        key_word,
        data_type='Top',
        count=10,
):
    set_proxy(proxy)
    set_cookie(cookie_to_dic(cookie))
    print(format_json(info))
```





