from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from utils.LDAPApi import ActiveDomain


class ADModelBackend(ModelBackend):
    """
    Rewrite
    Authenticates against settings.AUTH_USER_MODEL.
    """
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            if_ad_login = kwargs.get("if_ad_login", "")
            if if_ad_login:
                from .models import UserInfo
                # 1.判断当前用户名是否存在域中
                # 2.判断当前用户名是否存在系统用户表中
                try:
                    ui = UserInfo.objects.get(ad_user=username)
                    user = ui.user
                except UserInfo.DoesNotExist:
                    pass
                else:
                    if ActiveDomain.check_ad_user(username, password):
                        return user
            else:
                user = UserModel._default_manager.get_by_natural_key(username)

                if user.check_password(password):
                    return user
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
