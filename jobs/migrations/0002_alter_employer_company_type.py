# Generated by Django 4.2.11 on 2024-04-15 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employer',
            name='company_type',
            field=models.IntegerField(blank=True, choices=[(0, 'Công ty TNHH'), (1, 'Công ty Cổ phần'), (2, 'Công ty trách nhiệm hữu hạn một thành viên'), (3, 'Công ty tư nhân'), (4, 'Công ty liên doanh'), (5, 'Công ty tập đoàn')], null=True),
        ),
    ]