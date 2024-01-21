# Generated by Django 4.2.7 on 2024-01-02 02:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gentlelink", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tasks",
            name="deadline",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="tasks",
            name="status",
            field=models.CharField(
                choices=[("incomplete", "未完了"), ("complete", "完了")], max_length=20
            ),
        ),
    ]