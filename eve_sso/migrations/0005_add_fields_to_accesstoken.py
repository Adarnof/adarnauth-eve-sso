# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('eve_sso', '0004_drop_callbackcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='accesstoken',
            name='expires',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=utc), help_text='Datetime when access_token expires.'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='updated',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=utc), help_text='Datetime when this token was last updated'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='invalid',
            field=models.BooleanField(default=False, help_text='If true, this token is not valid anymore'),
        ),
        migrations.AddField(
            model_name='callbackredirect',
            name='allow_authentication',
            field=models.BooleanField(default=False, help_text='If true callback is allowed to authenticate the user'),
        ),
    ]
