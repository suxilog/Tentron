# Generated by Django 4.1.9 on 2023-05-30 03:06

from django.db import migrations
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faqitem',
            name='answer',
            field=wagtail.fields.RichTextField(),
        ),
    ]
