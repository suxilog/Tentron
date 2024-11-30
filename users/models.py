from django.contrib.auth.models import AbstractUser
from django.db import models

from organization.models import OrganizationMembership


class User(AbstractUser):
    # 添加自定义字段或方法
    organizations = models.ManyToManyField(
        "organization.Organization",
        through=OrganizationMembership,
        related_name="members",
        blank=True,
    )
