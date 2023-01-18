# Generated by Django 3.2.3 on 2023-01-18 08:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twbot', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actionforbotaccount',
            name='action',
        ),
        migrations.RemoveField(
            model_name='actionforbotaccount',
            name='object',
        ),
        migrations.RemoveField(
            model_name='actionforbotaccount',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='actionforotheraccount',
            name='action',
        ),
        migrations.RemoveField(
            model_name='actionforotheraccount',
            name='object',
        ),
        migrations.RemoveField(
            model_name='actionforotheraccount',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='actionfortargetaccount',
            name='action',
        ),
        migrations.RemoveField(
            model_name='actionfortargetaccount',
            name='object',
        ),
        migrations.RemoveField(
            model_name='actionfortargetaccount',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='actionfortargetaccount',
            name='tweet',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='tweet',
        ),
        migrations.RemoveField(
            model_name='competitoruserdetials',
            name='followers',
        ),
        migrations.RemoveField(
            model_name='competitoruserdetials',
            name='following',
        ),
        migrations.DeleteModel(
            name='EngageTask',
        ),
        migrations.RemoveField(
            model_name='phone',
            name='user',
        ),
        migrations.RemoveField(
            model_name='sms',
            name='number',
        ),
        migrations.RemoveField(
            model_name='tweetfortargetaccount',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='twitterjob',
            name='target_username',
        ),
        migrations.RemoveField(
            model_name='twitterjob',
            name='twitter_account',
        ),
        migrations.RemoveField(
            model_name='twitterjob',
            name='user',
        ),
        migrations.RemoveField(
            model_name='urlengagetask',
            name='avds',
        ),
        migrations.RemoveField(
            model_name='twitteraccount',
            name='other_following',
        ),
        migrations.DeleteModel(
            name='ActionForBotAccount',
        ),
        migrations.DeleteModel(
            name='ActionForOtherAccount',
        ),
        migrations.DeleteModel(
            name='ActionForTargetAccount',
        ),
        migrations.DeleteModel(
            name='ActionType',
        ),
        migrations.DeleteModel(
            name='Comment',
        ),
        migrations.DeleteModel(
            name='CompetitorUserDetials',
        ),
        migrations.DeleteModel(
            name='Phone',
        ),
        migrations.DeleteModel(
            name='Sms',
        ),
        migrations.DeleteModel(
            name='Tweet',
        ),
        migrations.DeleteModel(
            name='TweetForTargetAccount',
        ),
        migrations.DeleteModel(
            name='TwitterJob',
        ),
        migrations.DeleteModel(
            name='TwitterOtherAccount',
        ),
        migrations.DeleteModel(
            name='TwitterTargetAccount',
        ),
        migrations.DeleteModel(
            name='TwitterUser',
        ),
        migrations.DeleteModel(
            name='UrlEngageTask',
        ),
    ]
