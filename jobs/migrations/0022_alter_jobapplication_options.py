# Generated by Django 4.2.11 on 2024-07-18 09:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0021_remove_jobapplication_is_student_alter_user_role'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='jobapplication',
            options={'ordering': ['date', 'id']},
        ),
    ]