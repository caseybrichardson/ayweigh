from django.contrib import admin

from tracking.models import *


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    readonly_fields = [
        'external_id'
    ]


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    pass


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    pass


@admin.register(ContestantCheckIn)
class ContestantCheckInAdmin(admin.ModelAdmin):
    pass


@admin.register(CheckInPhoto)
class CheckInPhotoAdmin(admin.ModelAdmin):
    readonly_fields = [
        'external_id',
        'discord_id'
    ]
