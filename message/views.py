from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from wagtail.contrib.modeladmin.views import IndexView

from .models import MessageRecipient, TentronMessageTask


def index(request):
    return render(
        request,
        "message/index.html",
        {
            "tentron_messages": TentronMessageTask.objects.all(),
        },
    )


@login_required
def message_log_detail(request, message_log_id):
    message_log = get_object_or_404(MessageRecipient, id=message_log_id)
    if not request.user.is_superuser:
        message_log.mark_read()
    return render(
        request, "message/message_log_detail.html", {"message_log": message_log}
    )


class MessageTaskIndexView(IndexView):
    def dispatch(self, request, *args, **kwargs):

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect(self.url_helper.get_action_url("create"))
