from django.contrib import admin

from .models import Player, PlayerStat, Club


# Register your models here.
@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")  # Fields to display in the list view
    search_fields = ("name",)  # Fields to include in the search functionality
    ordering = ("name",)  # Default ordering of the list


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "position",
        "club",
        "slug",
    )  # Fields to display in the list view
    search_fields = (
        "name",
        "position",
        "club__name",
    )  # Fields to include in the search functionality
    list_filter = ("club",)  # Add filters for easy navigation
    ordering = ("name",)  # Default ordering of the list


@admin.register(PlayerStat)
class PlayerStatAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "competition",
        "goals",
        "assists",
    )  # Fields to display in the list view
    search_fields = (
        "player__name",
        "competition",
    )  # Fields to include in the search functionality
    list_filter = ("player", "competition")  # Add filters for easy navigation
    ordering = ("-player",)  # Default ordering of the list
