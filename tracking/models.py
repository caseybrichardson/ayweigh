import uuid

from django.db import models


# Utility Base Models


class TimeAuditable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DiscordIdentifiable(models.Model):
    discord_id = models.CharField(max_length=64)

    class Meta:
        abstract = True


class ExternallyIdentifiable(models.Model):
    external_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        abstract = True


# Tracking models


class Contest(TimeAuditable, ExternallyIdentifiable):
    name = models.CharField(max_length=128, blank=True)
    starting = models.DateField()
    check_in_period = models.PositiveSmallIntegerField(default=7)
    final_check_in = models.DateField()
    channel_id = models.CharField(max_length=64, null=True, blank=False)
    finished = models.BooleanField(default=False)


class Contestant(DiscordIdentifiable, TimeAuditable, ExternallyIdentifiable):
    contest = models.ForeignKey('tracking.Contest', null=True, related_name='contestants', on_delete=models.CASCADE)
    name = models.CharField(max_length=128, blank=False)


class CheckIn(ExternallyIdentifiable):
    contest = models.ForeignKey('tracking.Contest', related_name='check_ins', on_delete=models.CASCADE)
    starting = models.DateField()
    started_at = models.DateTimeField(null=True)
    thread_id = models.CharField(max_length=64, null=True, blank=False)
    finished = models.BooleanField(default=False)

    def __str__(self):
        return f'CheckIn({self.starting}, started: {self.started_at is not None})'


class ContestantCheckIn(DiscordIdentifiable, TimeAuditable, ExternallyIdentifiable):
    check_in = models.ForeignKey('tracking.CheckIn', related_name='contestant_check_ins', on_delete=models.CASCADE)
    contestant = models.ForeignKey('tracking.Contestant', related_name='check_ins', on_delete=models.CASCADE)
    weight = models.FloatField()


def check_in_photo_upload_dest(instance: 'CheckInPhoto', filename: str):
    contest_id = instance.contestant_check_in.check_in.contest.external_id
    check_in_date = instance.contestant_check_in.check_in.starting
    ext = filename.split('.')[-1]
    return f'{contest_id}/{check_in_date}/{instance.external_id}.{ext}'


class CheckInPhoto(DiscordIdentifiable, TimeAuditable, ExternallyIdentifiable):
    kind = models.CharField(max_length=32, blank=True)  # Used to identify scale shot, body shot, etc
    contestant_check_in = models.ForeignKey('tracking.ContestantCheckIn', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=check_in_photo_upload_dest)
