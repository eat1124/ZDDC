import json
from ldap3 import ALL_ATTRIBUTES, ALL, Connection, NTLM, Server
from django.conf import settings

AD_SERVER = settings.AD_SERVER
AD_USER = settings.AD_USER
AD_DOMAIN = settings.AD_DOMAIN
AD_PASSWORD = settings.AD_PASSWORD
AD_PORT = settings.AD_PORT


class ActiveDomain(object):
    """
    AD域类
    """
    def __init__(self):
        """
        初始化
        @param IP {string}: 域服务器地址
        @param PORT {int}: 域服务器端口
        @param USER {string}: 域服务器用户
        @param PASSWORD {string}: 域服务器密码
        """
        self.error = ""
        self.conn = None
        try:
            self.conn = Connection(
                server=[Server(AD_SERVER, port=AD_PORT, get_info=ALL, connect_timeout=5)],
                auto_bind=True,
                authentication=NTLM,  # 连接Windows AD需要配置此项
                read_only=False,
                user=AD_USER,  # 管理员账户
                password=AD_PASSWORD,
            )
        except Exception as e:
            self.error = "连接AD域服务器失败：{0}。".format(e)
        self.active_user_dn = 'CN=Users,DC={0},DC=com'.format(AD_DOMAIN)  # 【User】节点域
        self.user_filter = '(objectclass=user)'  # 只获取【用户】对象

    @property
    def users(self):
        """
        获取所有用户
        """
        users = []
        if self.conn:
            res = []
            try:
                self.conn.search(search_base=self.active_user_dn, search_filter=self.user_filter, attributes=ALL_ATTRIBUTES)
                res = self.conn.response_to_json()
                res = json.loads(res)['entries']
            except Exception as e:
                self.error = "获取AD域用户失败{0}。".format(e)
            for r in res:
                attributes = r["attributes"]
                name = attributes.get("name", "")
                if name:
                    users.append(name)
        return users


