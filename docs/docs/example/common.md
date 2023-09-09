# 通用采集

## common_crawler

通用采集（文章，评论采集）

### 参数

| 字段名        | 类型   | 必须 | 描述                                                         |
| ------------- | ------ | ---- | ------------------------------------------------------------ |
| task_id       | string | 是   | 文章id（https://twitter.com/elonmusk/status/1690164670441586688 中的 1690164670441586688） |
| data_type     | string | 是   | 采集类型（文章：article 评论：comment）                      |
| comment_count | int    | 否   | 采集评论数量（仅当data_type为comment时有效；默认不采集：-1，采集全部：0，采集指定的数量：>0） |

### 示例（已知文章id，采集此文章信息）

```python
from easy_spider_tool import cookie_to_dic, format_json
from easy_twitter_crawler import set_proxy, set_cookie, common_crawler

set_proxy(proxy)
set_cookie(cookie_to_dic(cookie))

for info in common_crawler(
        '1684447438864785409',
        data_type='article',
):
    set_proxy(proxy)
    set_cookie(cookie_to_dic(cookie))
    print(format_json(info))
```



### 示例（已知文章id，采集此文章下10条评论）

```python
from easy_spider_tool import cookie_to_dic, format_json
from easy_twitter_crawler import set_proxy, set_cookie, common_crawler

set_proxy(proxy)
set_cookie(cookie_to_dic(cookie))

for info in common_crawler(
        '1684447438864785409',
        data_type='comment',
        comment_count=10,
):
    set_proxy(proxy)
    set_cookie(cookie_to_dic(cookie))
    print(format_json(info))
```

