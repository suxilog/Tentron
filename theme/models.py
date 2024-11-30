import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

User = get_user_model()


class Theme(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_common = models.BooleanField(default=False)
    user = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Theme"
        verbose_name_plural = "Themes"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        # 创建对应的模板目录
        template_dir = os.path.join(settings.BASE_DIR, "theme", "templates", self.slug)
        static_template_dir = os.path.join(
            settings.BASE_DIR, "theme", "static", "templates", self.slug
        )
        os.makedirs(template_dir, exist_ok=True)
        os.makedirs(static_template_dir, exist_ok=True)

    @classmethod
    def accessible_to(cls, user):
        return cls.objects.filter(Q(user=user) | Q(is_common=True))
