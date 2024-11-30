from curses import panel
from tabnanny import verbose

from django import forms
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.admin.widgets import AdminAutoHeightTextInput
from wagtail.fields import RichTextField
from wagtailmodelchooser import Chooser, register_model_chooser


class MessageForm(WagtailAdminModelForm):

    send_to_all = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields["sender"]
        self.initial = {"sender": self.for_user}
        if not self.for_user.is_superuser:

            pass

    @transaction.atomic
    def save(self, commit=True):
        self.instance.sender = self.for_user
        model = super().save(commit=commit)
        if self.for_user.is_superuser and self.cleaned_data.get("send_to_all"):
            recipients = get_user_model().objects.exclude(is_superuser=True)
        elif not self.for_user.is_superuser:
            recipients = get_user_model().objects.filter(is_superuser=True)

        else:
            recipients = [
                form.instance.recipient for form in self.formsets["message_recipients"]
            ]
        if commit:
            model.save()
            for recipient in recipients:
                MessageRecipient.objects.get_or_create(
                    message=model, recipient=recipient
                )

        return model


class MessageContent(models.Model):
    message = ParentalKey(
        "TentronMessageTask", on_delete=models.CASCADE, related_name="message_contents"
    )
    title = models.CharField(max_length=255)
    content = RichTextField()


class MessageRecipient(models.Model):
    message = ParentalKey(
        "TentronMessageTask",
        on_delete=models.CASCADE,
        related_name="message_recipients",
    )
    recipient = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="received_messages"
    )
    read_at = models.DateTimeField(null=True, blank=True)
    panels = [
        FieldPanel("recipient"),
    ]

    def __str__(self):
        # First name Last name (username)
        return f"{self.recipient.first_name} {self.recipient.last_name} ({self.recipient.username})"

    def sender(self):
        return self.message.sender

    def title(self):
        return self.message.message_contents.first().title

    def content(self):
        # mark safe

        return self.message.message_contents.first().content

    def sent_at(self):
        return self.message.sent_at

    def mark_read(self):
        self.read_at = timezone.now()
        self.save()

    class Meta:
        unique_together = ("message", "recipient")
        verbose_name = "Message log"


class TentronMessageTask(ClusterableModel, models.Model):
    base_form_class = MessageForm
    MESSAGE_TYPES = (
        ("announcement", "Announcement"),
        ("activity", "Activity"),
        ("news", "News"),
        ("other", "Other"),
        # Add more types as needed
    )

    sender = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="sent_messages"
    )

    sent_at = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(
        max_length=255, choices=MESSAGE_TYPES, default="other"
    )
    panels = [
        FieldPanel("sender"),
        InlinePanel("message_recipients", label="Recipients", min_num=0),
        InlinePanel("message_contents", label="Content", min_num=1, max_num=1),
        FieldPanel("message_type", permission="superuser"),
        FieldPanel("send_to_all", permission="superuser"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["message"] = self
        print(context)
        return context

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def recipients(self):
        # 5 recipients name max
        return ", ".join(
            [r.recipient.username for r in self.message_recipients.all()[:5]]
        )


@register_model_chooser
class MessageRecipientChooser(Chooser):
    model = get_user_model()
    # model_template = "wagtailmodelchooser/modal.html"
    # modal_results_template = "wagtailmodelchooser/results.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.exclude(pk=request.user.pk)
        else:
            return qs.filter(is_superuser=True)
