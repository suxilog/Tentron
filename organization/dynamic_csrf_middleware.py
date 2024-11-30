from django.conf import settings
from django.utils.functional import SimpleLazyObject


def get_csrf_trusted_origins(request):
    # 在这里根据您的多租户逻辑动态设置CSRF_TRUSTED_ORIGINS
    # 例如，可以根据请求的域名或其他条件来设置
    # 返回一个字符串列表，包含允许的域名或来源

    # 示例：返回当前请求的站点的域名
    current_site = request.site
    domain = current_site.domain if current_site else None

    return [domain] if domain else []


class DynamicCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 动态设置CSRF_TRUSTED_ORIGINS
        csrf_trusted_origins = SimpleLazyObject(
            lambda: get_csrf_trusted_origins(request)
        )
        setattr(request, "CSRF_TRUSTED_ORIGINS", csrf_trusted_origins)

        response = self.get_response(request)
        return response
