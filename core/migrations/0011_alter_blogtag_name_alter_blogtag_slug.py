# Generated by Django 4.1.9 on 2023-06-13 01:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_alter_blogtag_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogtag',
            name='name',
            field=models.CharField(max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='blogtag',
            name='slug',
            field=models.SlugField(allow_unicode=True, max_length=100, verbose_name='slug'),
        ),
    ]
