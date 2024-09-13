# Generated by Django 4.2.13 on 2024-08-22 13:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('server_check_interval', models.IntegerField(default=30, help_text='Interval in seconds for checking server status.')),
                ('display_name', models.CharField(blank=True, max_length=100)),
                ('email', models.EmailField(blank=True, max_length=255)),
                ('preferred_language', models.CharField(choices=[('en', 'English'), ('fr', 'French'), ('de', 'German')], default='en', max_length=50)),
                ('timezone', models.CharField(default='UTC', max_length=50)),
                ('theme', models.CharField(choices=[('light', 'Light'), ('dark', 'Dark')], default='light', max_length=10)),
                ('font_size', models.CharField(choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], default='medium', max_length=10)),
                ('primary_color', models.CharField(default='#2980b9', max_length=7)),
                ('email_notifications', models.BooleanField(default=True)),
                ('push_notifications', models.BooleanField(default=True)),
                ('two_factor_authentication', models.BooleanField(default=False)),
                ('scheduled_lights', models.BooleanField(default=False)),
                ('eco_mode', models.BooleanField(default=False)),
                ('m5core2_ip', models.CharField(blank=True, default='', max_length=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('user', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Light',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=100)),
                ('description', models.TextField(blank=True, default='', null=True)),
                ('state', models.IntegerField(choices=[(1, 'on'), (2, 'off'), (3, 'timer')], default=2)),
                ('choices', models.ManyToManyField(blank=True, related_name='lights', to='light_app.choice')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lights', to='light_app.room')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
