from django.urls import path

from .views import message_log_detail

app_name = "message"
urlpatterns = [
    # ...
    path(
        "message_log/<int:message_log_id>/",
        message_log_detail,
        name="message_log_detail",
    ),
    # ...
]
