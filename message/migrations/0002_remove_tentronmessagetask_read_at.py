# Generated by Django 4.1.9 on 2023-06-19 06:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tentronmessagetask',
            name='read_at',
        ),
    ]