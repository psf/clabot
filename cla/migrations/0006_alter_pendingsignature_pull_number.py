# Generated by Django 5.2 on 2025-04-18 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cla", "0005_remove_pendingsignature_ref"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pendingsignature",
            name="pull_number",
            field=models.IntegerField(default=-1),
            preserve_default=False,
        ),
    ]
