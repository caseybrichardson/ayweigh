# Generated by Django 4.1 on 2022-08-22 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contestantcheckin',
            name='message_text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contestantcheckin',
            name='units',
            field=models.CharField(default='lbs', max_length=16),
            preserve_default=False,
        ),
    ]
