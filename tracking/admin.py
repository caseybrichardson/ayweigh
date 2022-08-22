from django.contrib import admin

from tracking.models import *


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    readonly_fields = [
        'external_id',
        'updated_at',
        'created_at'
    ]

    list_display = [
        'id',
        'name',
        'starting',
        'final_check_in',
        'updated_at',
        'created_at'
    ]


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    readonly_fields = [
        'external_id'
    ]

    list_display = [
        'id',
        'starting',
        'finished'
    ]


@admin.register(Contestant)
class ContestantAdmin(admin.ModelAdmin):
    readonly_fields = [
        'external_id',
        'discord_id',
        'updated_at',
        'created_at'
    ]

    list_display = [
        'id',
        'name',
        'discord_id',
        'updated_at',
        'created_at'
    ]


@admin.register(ContestantCheckIn)
class ContestantCheckInAdmin(admin.ModelAdmin):
    readonly_fields = [
        'external_id',
        'discord_id',
        'updated_at',
        'created_at'
    ]

    list_display = [
        'id',
        'discord_id',
        'updated_at',
        'created_at'
    ]


@admin.register(CheckInPhoto)
class CheckInPhotoAdmin(admin.ModelAdmin):
    readonly_fields = [
        'external_id',
        'discord_id',
        'updated_at',
        'created_at'
    ]

    list_display = [
        'id',
        'updated_at',
        'created_at'
    ]
