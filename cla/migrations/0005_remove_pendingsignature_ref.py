# Generated by Django 5.2 on 2025-04-18 12:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cla", "0004_pendingsignature_pull_number"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pendingsignature",
            name="ref",
        ),
    ]
