# Generated by Django 4.2.7 on 2023-11-30 09:11

import app.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256, unique=True)),
                ('pub_date', models.DateTimeField(verbose_name='date published')),
                ('description', models.TextField()),
                ('check_script', models.FileField(upload_to=app.models.challenge_directory_path)),
                ('needs_approval', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='DockerImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('ssh_port', models.IntegerField(default=30000, unique=True)),
                ('conatiners_limit', models.IntegerField(default=30)),
                ('reuse_container', models.BooleanField(default=False)),
                ('docker_file', models.FileField(upload_to=app.models.dockerimage_directory_path)),
                ('docker_image_id', models.CharField(default='0', max_length=12)),
                ('optional_docker_ports', models.CharField(blank=True, default='', max_length=256)),
                ('optional_docker_volumes', models.TextField(blank=True, default='')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(max_length=64)),
                ('full_name', models.CharField(max_length=256)),
                ('email', models.CharField(max_length=256)),
                ('group', models.CharField(blank=True, default='', max_length=32)),
                ('role', models.CharField(choices=[('T', 'Teacher'), ('S', 'Student')], default='S', max_length=1)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to=app.models.user_directory_path)),
                ('teacher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.user')),
            ],
        ),
        migrations.CreateModel(
            name='DockerContainer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('container_id', models.CharField(default='0', max_length=128)),
                ('challenge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.challenge')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.user')),
            ],
        ),
        migrations.AddField(
            model_name='challenge',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.user'),
        ),
        migrations.AddField(
            model_name='challenge',
            name='docker_image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.dockerimage'),
        ),
    ]
