# Generated by Django 5.2.1 on 2025-06-04 08:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trophies', '0004_alter_trophy_options_alter_usertrophy_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='trophy',
            options={'ordering': ['id'], 'verbose_name': '트로피', 'verbose_name_plural': '트로피 목록'},
        ),
        migrations.AlterModelOptions(
            name='usertrophy',
            options={'ordering': ['-awarded_at'], 'verbose_name': '사용자 트로피', 'verbose_name_plural': '사용자 트로피 목록'},
        ),
    ]
