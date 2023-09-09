import inspect
from typing import Union


class TwitterFilter:
    __word_category_format = {
        'exact': '"{}"',
        'filter_any': '({})',  # 原为any 关键词冲突
        'exclude': '-{}',
        'tab': '(#{})',
        'lang': 'lang:{}',
    }
    __account_category_format = {
        'filter_from': 'from:{}',  # 原为from 后加()
        'to': 'to:{}',  # 后加()
        '@': '@:{}',  # 后加()
    }
    __filter_category_format = {
        'only_replies': 'filter:replies',
        'only_links': 'filter:links',
        'exclude_replies': '-filter:replies',
        'exclude_links': '-filter:links',
    }
    __interact_category_format = {
        'min_replies': 'min_replies:{}',
        'min_faves': 'min_faves:{}',
        'min_retweets': 'min_retweets:{}',
        'min_read': 'min_retweets:{}',
    }
    __date_category_format = {
        'since': 'since:{}',  # since:2010-06-13
        'until': 'until:{}'
    }

    def __init__(self, key_word: str):
        self.key_word = key_word
        self.__fill_keyword = None
        self.__word_category_dataset = []
        self.__account_category_dataset = []
        self.__filter_category_dataset = []
        self.__interact_category_dataset = []
        self.__date_category_dataset = []

    def filter_join(self) -> str:
        """过滤条件拼接"""

        filter_join_dateset = [
            *self.__word_category_dataset,
            *self.__account_category_dataset,
            *self.__filter_category_dataset,
            *self.__interact_category_dataset,
            *self.__date_category_dataset,
        ]

        if self.__fill_keyword is None:
            filter_join_dateset.insert(0, self.key_word)

        return ' '.join(filter_join_dateset)

    def word_category(self, exact: str = None, filter_any: str = None,
                      exclude: str = None,
                      tab: str = None, lang: str = None):
        """词语过滤器"""
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        args.remove('self')

        values = dict(values)
        for arg in args:
            if values[arg] is not None:  # 代表有key，但是没值
                if values[arg] == '':
                    self.__fill_keyword = False
                    values[arg] = [self.key_word]
                elif not values[arg].startswith('"'):
                    values[arg] = values[arg].split()
                else:
                    values[arg] = [values[arg]]

                for i in values[arg]:
                    key_join = self.__word_category_format[arg].format(i)
                    if key_join:
                        self.__word_category_dataset.append(key_join)

        return self.__word_category_dataset

    def account_category(self, filter_from: str = None, to: str = None,
                         at: str = None):
        """账户过滤器"""

        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        args.remove('self')

        values = dict(values)
        for arg in args:
            if values[arg] is not None:
                if not values[arg].startswith('"'):
                    values[arg] = values[arg].split()
                else:
                    values[arg] = [values[arg]]

                key_join = ' OR '.join([self.__account_category_format[arg].format(i) for i in values[arg]])

                if key_join:
                    self.__account_category_dataset.append('(' + key_join + ')')

        return self.__account_category_dataset

    def filter_category(self, only_replies: str = None, only_links: str = None, exclude_replies: str = None,
                        exclude_links: str = None):
        """过滤过滤器"""

        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        args.remove('self')

        values = dict(values)
        for arg in args:
            if values[arg] is not None:
                key_join = self.__filter_category_format[arg].format(values[arg])
                self.__filter_category_dataset.append(key_join)

        return self.__filter_category_dataset

    def interact_category(self, min_replies: Union[str, int] = None, min_faves: Union[str, int] = None,
                          min_retweets: Union[str, int] = None, **kwargs):
        """互动量过滤器"""

        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        args.remove('self')

        values = dict(values)
        for arg in args:
            if values[arg] is not None:
                if values[arg] != '' and arg in self.__interact_category_format:
                    key_join = self.__interact_category_format[arg].format(values[arg])
                    self.__interact_category_dataset.append(key_join)

        return self.__interact_category_dataset

    def extend_interact_category(self, min_read: Union[str, int] = None):
        """扩展互动量过滤器"""
        return min_read

    def date_category(self, since: str = None, until: str = None):
        """日期过滤器"""

        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        args.remove('self')

        values = dict(values)
        for arg in args:
            if values[arg] is not None:
                if values[arg] != '':
                    key_join = self.__date_category_format[arg].format(values[arg])
                    self.__date_category_dataset.append(key_join)

        return self.__date_category_dataset
