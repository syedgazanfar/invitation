"""
Add is_approved field to User model for admin approval workflow
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_current_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_approved',
            field=models.BooleanField(
                default=False,
                help_text='User account approved by admin after payment verification'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='approved_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When the user was approved'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='approved_users',
                to='accounts.user',
                help_text='Admin who approved this user'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='payment_verified',
            field=models.BooleanField(
                default=False,
                help_text='Payment has been verified by admin'
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='notes',
            field=models.TextField(
                blank=True,
                help_text='Admin notes about this user'
            ),
        ),
    ]
