"""
自定义异常类
"""
from enum import Enum


class ErrorCode(Enum):
    """异常错误码"""
    pass


class AccountErrorCode(ErrorCode):
    pass


class ProxyException(Exception):
    """
    代理异常
    """
    pass


class CaptchaException(Exception):
    """
    验证异常
    """
    pass


class UserException(Exception):
    """
    用户异常信息
    """

    def __init__(self, user, msg: str = ''):
        self.user = user
        self.msg = msg

    def __str__(self):
        return f'【{self.user}】: {self.msg}'


class UserLoginException(UserException):
    """用户登录异常"""

    def __str__(self):
        return f'【{self.user}】 : 该用户信息采集需要登录'


class UserLoseException(UserException):
    """账户不存在"""

    def __str__(self):
        return f'【{self.user}】: 该账号不存在'


class UserPrivateException(UserException):
    """用户私密"""

    def __str__(self):
        return f'【{self.user}】 : 该用户已设置为私密，无法采集'


class UserSuspendedException(UserException):
    """用户封禁"""

    def __str__(self):
        return f'【{self.user}】 : 该用户已被封禁，无法采集'


class ArticleException(Exception):
    """文章异常信息"""

    def __init__(self, article_id: str, msg: str = ''):
        self.article_id = article_id
        self.msg = msg

    def __str__(self):
        return f'【{self.article_id}】: {self.msg}'


class ArticleLoginException(ArticleException):
    """文章登录异常"""

    def __str__(self):
        return f'【{self.article_id}】: 该推文采集需要登录'
