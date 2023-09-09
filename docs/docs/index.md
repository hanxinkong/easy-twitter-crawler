# easy_twitter_crawler

推特（Twitter）采集程序，支持元搜索,用户,粉丝,关注,发文,回复,评论采集，希望能为使用者带来益处。如果您也想贡献好的代码片段，请将代码以及描述，通过邮箱（ [xinkonghan@gmail.com](mailto:hanxinkong<xinkonghan@gmail.com>)
）发送给我。代码格式是遵循自我主观，如存在不足敬请指出！

----
**文档地址：
** <a href="https://easy-twitter-crawler.xink.top/" target="_blank">https://easy-twitter-crawler.xink.top/ </a>

**PyPi地址：
** <a href="https://pypi.org/project/easy-twitter-crawler" target="_blank">https://pypi.org/project/easy-twitter-crawler </a>

**GitHub地址：** [https://github.com/hanxinkong/easy-twitter-crawler](https://github.com/hanxinkong/easy-twitter-crawler)

----

## 推特三件套（有需要可自行安装）

- `easy_twitter_publisher` 推特发帖,回帖,转载 https://pypi.org/project/easy-twitter-publisher
- `easy_twitter_crawler` 推特采集 https://pypi.org/project/easy-twitter-crawler
- `easy_twitter_interactors` 推特互动（点赞,刷阅读量等） https://pypi.org/project/easy-twitter-interactors

## 安装

<div class="termy">

```console
pip install easy-twitter-crawler
```

</div>

## 主要功能

- `search_crawler` 关键词搜索采集（支持热门,用户,最新,视频,照片;支持条件过滤）
- `user_crawler` 用户采集（支持用户信息,用户粉丝和关注,用户发文,用户回复）
- `common_crawler` 通用采集（支持发文,评论）

## 简单使用

设置代理及cookie (关键词,用户发文,用户回复,评论需要设置cookie)

```python
proxy = {
    'http': 'http://127.0.0.1:10808',
    'https': 'http://127.0.0.1:10808'
}
cookie = 'auth_token=686fa28f49400698820d0a3c344c51efdeeaf73a; ct0=5bed99b7faad9dcc742eda564ddbcf37888f8794abd6d4d736919234440be2172da1e9a9fc48bb068db1951d1748ba5467db2bc3e768f122794265da0a9fa6135b4ef40763e7fd91f730d0bb1298136b'
```

关键词采集使用案例（对关键词指定条件采集10条数据）

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

关键词采集参数说明

| 字段名       | 类型     | 必须 | 描述                                                            |
|-----------|--------|----|---------------------------------------------------------------|
| key_word  | string | 是  | 关键词                                                           |
| data_type | string | 否  | 指定采集的板块，大小写均可（热门：Top 用户：People 最新：Latest 视频：Videos 照片：Photos） |
| count     | int    | 否  | 采集的数量（默认不采集：-1，采集全部：0，采集指定的数量：>0）                             |                                 

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

----

用户信息采集使用案例（采集该用户信息及10条文章，10条回复，10个粉丝信息，10个关注信息）

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

用户信息采集参数说明

| 字段名             | 类型     | 必须 | 描述                                            |
|-----------------|--------|----|-----------------------------------------------|
| user_id         | string | 是  | 用户名（https://twitter.com/elonmusk 中的 elonmusk） |
| article_count   | int    | 否  | 采集文章数（默认不采集：-1，采集全部：0，采集指定的数量：>0）             |             
| reply_count     | int    | 否  | 采集回复数 （默认不采集：-1，采集全部：0，采集指定的数量：>0）            |              
| following_count | int    | 否  | 采集关注数 （默认不采集：-1，采集全部：0，采集指定的数量：>0）            |                
| followers_count | int    | 否  | 采集粉丝数 （默认不采集：-1，采集全部：0，采集指定的数量：>0）            |                
| start_time      | string | 否  | 数据截取开始时间 （仅当采集文章或回复时有效）                       |                   
| end_time        | string | 否  | 数据截取结束时间（仅当采集文章或回复时有效）                        |                  

___

通用采集使用案例（已知文章id，采集此文章信息）

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

通用采集使用案例（已知文章id，采集此文章下10条评论）

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

通用采集参数说明

| 字段名           | 类型     | 必须 | 描述                                                                                   |
|---------------|--------|----|--------------------------------------------------------------------------------------|
| task_id       | string | 是  | 文章id（https://twitter.com/elonmusk/status/1690164670441586688 中的 1690164670441586688） |
| data_type     | string | 是  | 采集类型（文章：article 评论：comment）                                                          |             
| comment_count | int    | 否  | 采集评论数量（仅当data_type为comment时有效；默认不采集：-1，采集全部：0，采集指定的数量：>0）                            |             

___

## 语言表

| 语言代码 | 语言名称       | 英文名                          |
|------|------------|------------------------------|
| aa   | 阿法尔语       | Afar                         |
| ab   | 阿布哈兹语      | Abkhaz language              |
| ae   | 阿维斯陀语      | Avestan language             |
| af   | 南非语        | Afrikaans                    |
| ak   | 阿坎语        | Arkan language               |
| am   | 阿姆哈拉语      | Amharic                      |
| an   | 阿拉贡语       | Aragonese                    |
| ar   | 阿拉伯语       | Arabic                       |
| as   | 阿萨姆语       | Assam                        |
| av   | 阿瓦尔语       | Avar language                |
| ay   | 艾马拉语       | Aymara                       |
| az   | 阿塞拜疆语      | Azerbaijani                  |
| ba   | 巴什基尔语      | Bashkir                      |
| be   | 白俄罗斯语      | Belarusian                   |
| bg   | 保加利亚语      | Bulgarian                    |
| bh   | 比哈尔语       | Bihar                        |
| bi   | 比斯拉马语      | Bislama                      |
| bm   | 班巴拉语       | Bambara                      |
| bn   | 孟加拉语       | Bengali                      |
| bo   | 藏语         | Tibetan language             |
| br   | 布列塔尼语      | Breton                       |
| bs   | 波斯尼亚语      | Bosnian                      |
| ca   | 加泰隆语       | Catalan                      |
| ce   | 车臣语        | Chechen                      |
| ch   | 查莫罗语       | Chamorro                     |
| co   | 科西嘉语       | Corsican language            |
| cr   | 克里语        | Kerry                        |
| cs   | 捷克语        | Czech                        |
| cu   | 古教会斯拉夫语    | Ancient Church Slavic        |
| cv   | 楚瓦什语       | Chuvash language             |
| cy   | 威尔士语       | Welsh                        |
| da   | 丹麦语        | Danish                       |
| de   | 德语         | German                       |
| dv   | 迪维希语       | Dhivehi language             |
| dz   | 不丹语        | Bhutanese                    |
| ee   | 埃维语        | Ewe language                 |
| el   | 现代希腊语      | Modern Greek                 |
| en   | 英语         | English                      |
| eo   | 世界语        | Esperanto                    |
| es   | 西班牙语       | Spanish                      |
| et   | 爱沙尼亚语      | Estonian                     |
| eu   | 巴斯克语       | Basque                       |
| fa   | 波斯语        | Persian                      |
| ff   | 富拉语        | Fulah language               |
| fi   | 芬兰语        | Finnish                      |
| fj   | 斐济语        | Fijian                       |
| fo   | 法罗语        | Faroese                      |
| fr   | 法语         | French                       |
| fy   | 弗里西亚语      | Frisian                      |
| ga   | 爱尔兰语       | Irish                        |
| gd   | 苏格兰盖尔语     | Scottish Gaelic              |
| gl   | 加利西亚语      | Galician                     |
| gn   | 瓜拉尼语       | Guarani                      |
| gu   | 古吉拉特语      | Gujarati                     |
| gv   | 马恩岛语       | Manx language                |
| ha   | 豪萨语        | Hausa                        |
| he   | 希伯来语       | Hebrew                       |
| hi   | 印地语        | Hindi                        |
| ho   | 希里莫图语      | Greek language               |
| hr   | 克罗地亚语      | Croatian                     |
| ht   | 海地克里奥尔语    | Haitian Creole               |
| hu   | 匈牙利语       | Hungarian                    |
| hy   | 亚美尼亚语      | Armenian                     |
| hz   | 赫雷罗语       | Herero                       |
| ia   | 国际语 A      | Interlingua                  |
| id   | 印尼语        | Indonesian                   |
| ie   | 国际语 E      | Interlingua E                |
| ig   | 伊博语        | Ibo language                 |
| ii   | 四川彝语（诺苏语）  | Sichuan Yi (Nuosu)           |
| ik   | 依努庇克语      | According to Nupian language |
| io   | 伊多语        | Ido language                 |
| is   | 冰岛语        | Icelandic                    |
| it   | 意大利语       | Italian                      |
| iu   | 因纽特语       | Inuit language               |
| ja   | 日语         | Japanese                     |
| jv   | 爪哇语        | Javanese                     |
| ka   | 格鲁吉亚语      | Georgian                     |
| kg   | 刚果语        | Congo                        |
| ki   | 基库尤语       | Kikuyu                       |
| kj   | 宽亚玛语       | Aum wide language            |
| kk   | 哈萨克语       | Kazakh                       |
| kl   | 格陵兰语       | Greenlandic                  |
| km   | 高棉语        | Cambodian                    |
| kn   | 卡纳达语       | Kannada                      |
| ko   | 朝鲜语、韩语     | Korean, Korean               |
| kr   | 卡努里语       | Canouli                      |
| ks   | 克什米尔语      | Kashmir                      |
| ku   | 库尔德语       | Kurdish                      |
| kv   | 科米语        | Komi                         |
| kw   | 康沃尔语       | Cornish                      |
| ky   | 吉尔吉斯语      | Kyrgyz language              |
| la   | 拉丁语        | Latin                        |
| lb   | 卢森堡语       | Luxembourgish                |
| lg   | 卢干达语       | Lugan da language            |
| li   | 林堡语        | Limburg                      |
| ln   | 林加拉语       | Lingala                      |
| lo   | 老挝语        | Lao                          |
| lt   | 立陶宛语       | Lithuanian                   |
| lu   | 卢巴语        | Luba                         |
| lv   | 拉脱维亚语      | Latvian                      |
| mg   | 马达加斯加语     | Madagascar                   |
| mh   | 马绍尔语       | Marshall language            |
| mi   | 毛利语        | Maori language               |
| mk   | 马其顿语       | Macedonian                   |
| ml   | 马拉亚拉姆语     | Malayalam                    |
| mn   | 蒙古语        | Mongolian                    |
| mo   | 摩尔达维亚语     | Moldavian                    |
| mr   | 马拉提语       | Marathi                      |
| ms   | 马来语        | Malay                        |
| mt   | 马耳他语       | Maltese                      |
| my   | 缅甸语        | Burmese                      |
| na   | 瑙鲁语        | Nauru language               |
| nb   | 书面挪威语      | Written Norwegian            |
| nd   | 北恩德贝勒语     | North Ndebele                |
| ne   | 尼泊尔语       | Nepali language              |
| ng   | 恩敦加语       | Ennastatic                   |
| nl   | 荷兰语        | Dutch                        |
| nn   | 新挪威语       | New Norwegian                |
| no   | 挪威语        | Norwegian                    |
| nr   | 南恩德贝勒语     | South End Baylor             |
| nv   | 纳瓦霍语       | Navajo                       |
| ny   | 尼扬贾语       | Nyanja                       |
| oc   | 奥克语        | Och                          |
| oj   | 奥吉布瓦语      | Ojibwa                       |
| om   | 奥洛莫语       | Olomouc                      |
| or   | 奥利亚语       | Oriya                        |
| os   | 奥塞梯语       | Ossetian language            |
| pa   | 旁遮普语       | Punjabi                      |
| pi   | 巴利语        | Pali                         |
| pl   | 波兰语        | Polish                       |
| ps   | 普什图语       | Pashto                       |
| pt   | 葡萄牙语       | Portuguese                   |
| qu   | 凯楚亚语       | Kai Chu Asian                |
| rm   | 罗曼什语       | Romansh language             |
| rn   | 基隆迪语       | Kirundi                      |
| ro   | 罗马尼亚语      | Romanian                     |
| ru   | 俄语         | Russian                      |
| rw   | 卢旺达语       | Rwanda                       |
| sa   | 梵语         | Sanskrit                     |
| sc   | 萨丁尼亚语      | Sardinian                    |
| sd   | 信德语        | Sindhi language              |
| se   | 北萨米语       | Northern Sami                |
| sg   | 桑戈语        | Sango language               |
| sh   | 塞尔维亚-克罗地亚语 | Serbian - Croatian           |
| si   | 僧加罗语       | Sinhala                      |
| sk   | 斯洛伐克语      | Slovak                       |
| sl   | 斯洛文尼亚语     | Slovenian                    |
| sm   | 萨摩亚语       | Samoan                       |
| sn   | 绍纳语        | Shona language               |
| so   | 索马里语       | Somali                       |
| sq   | 阿尔巴尼亚语     | Albanian                     |
| sr   | 塞尔维亚语      | Serbian                      |
| ss   | 斯瓦特语       | Swat                         |
| st   | 南索托语       | South Sotho                  |
| su   | 巽他语        | He language                  |
| sv   | 瑞典语        | Swedish                      |
| sw   | 斯瓦希里语      | Swahili                      |
| ta   | 泰米尔语       | Tamil                        |
| te   | 泰卢固语       | Telugu                       |
| tg   | 塔吉克斯坦语     | Tajikistan                   |
| th   | 泰语         | Thai                         |
| ti   | 提格里尼亚语     | Tigrinya                     |
| tk   | 土库曼语       | Turkmen                      |
| tl   | 他加禄语       | Tagalog                      |
| tn   | 塞茨瓦纳语      | Sethwana                     |
| to   | 汤加语        | Tongan                       |
| tr   | 土耳其语       | Turkish                      |
| ts   | 宗加语        | Zong dialect                 |
| tt   | 塔塔尔语       | Tatar                        |
| tw   | 特威语        | Twain language               |
| ty   | 塔希提语       | Tahitian                     |
| ug   | 维吾尔语       | Uyghur                       |
| uk   | 乌克兰语       | Ukrainian                    |
| ur   | 乌尔都语       | Urdu                         |
| uz   | 乌兹别克语      | Uzbek                        |
| ve   | 文达语        | Vinda                        |
| vi   | 越南语        | Vietnamese                   |
| vo   | 沃拉普克语      | Volapuk                      |
| wa   | 沃伦语        | Warren                       |
| wo   | 沃洛夫语       | Wolof                        |
| xh   | 科萨语        | Xhosa                        |
| yi   | 依地语        | Yiddish                      |
| yo   | 约鲁巴语       | Yoruba                       |
| za   | 壮语         | Zhuang                       |
| zh   | 中文（汉语）     | Chinese                      |
| zu   | 祖鲁语        | Zulu                         |

## 依赖

内置依赖

- `re` Provides regular expression related functions for matching and processing text data.
- `time` Python Datetime module supplies classes to work with date and time.
- `datetime` Python Datetime module supplies classes to work with date and time.
- `itertools` Secure hash and messag e digest algorithm library.
- `typing` Type Hints for Python.
- `enum` Type Hints for Python.
- `json` Type Hints for Python.
- `asyncio` Type Hints for Python.
- `functools` Type Hints for Python.
- `math` Type Hints for Python.
- `urllib` Type Hints for Python.

第三方依赖

- `requests_html` An XPath for JSON.
- `requests` Python library used for parsing dates from natural language text.
- `loguru` Python library used for working with timezone information.
- `easy_spider_tool` Python library used for working with timezone information.
- `my_fake_useragent` Python library used for working with timezone information.
- `urllib3` Python library used for working with timezone information.
- `inspect` Python library used for working with timezone information.

_注：依赖顺序排名不分先后_

## 许可证

该项目根据 **MIT** 许可条款获得许可.

## 链接

Github：https://github.com/hanxinkong/easy-twitter-crawler

在线文档：https://easy-twitter-crawler.xink.top

## 贡献者
