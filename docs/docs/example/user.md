# 用户

## user_crawler

用户信息，发文，回复，粉丝，关注采集

### 参数


| 字段名             | 类型     | 必须 | 描述                                            |
|-----------------|--------|----|-----------------------------------------------|
| user_id         | string | 是  | 用户名（https://twitter.com/elonmusk 中的 elonmusk） |
| article_count   | int    | 否  | 采集文章数（默认不采集：-1，采集全部：0，采集指定的数量：>0）             |             
| reply_count     | int    | 否  | 采集回复数 （默认不采集：-1，采集全部：0，采集指定的数量：>0）            |              
| following_count | int    | 否  | 采集关注数 （默认不采集：-1，采集全部：0，采集指定的数量：>0）            |                
| followers_count | int    | 否  | 采集粉丝数 （默认不采集：-1，采集全部：0，采集指定的数量：>0）            |                
| start_time      | string | 否  | 数据截取开始时间 （仅当采集文章或回复时有效）                       |                   
| end_time        | string | 否  | 数据截取结束时间（仅当采集文章或回复时有效）                        |                  

### 示例（采集该用户信息及10条文章，10条回复，10个粉丝信息，10个关注信息）

```python
from easy_spider_tool import cookie_to_dic, format_json
from easy_twitter_crawler import set_proxy, set_cookie, user_crawler

set_proxy(proxy)
set_cookie(cookie_to_dic(cookie))

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
    print(format_json(info))
    print(f"文章数：{len(info.get('article', []))}")
    print(f"粉丝数：{len(info.get('followers', []))}")
    print(f"关注数：{len(info.get('following', []))}")
    print(f"回复数：{len(info.get('reply', []))}")
```





