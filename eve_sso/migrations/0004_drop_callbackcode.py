# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('eve_sso', '0003_cleanup_accesstoken'),
    ]

    operations = [
        # CallbackCode is not used anymore
        migrations.DeleteModel(
            name='CallbackCode',
        ),
    ]
