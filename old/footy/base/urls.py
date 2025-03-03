from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("players-all/", views.players_all, name="players_all"),
    path("player-stats/<slug:slug>/", views.player_stats, name="player_stats"),
    path(
        "player-stats/<slug:slug>/graph/", views.generate_graph, name="generate_graph"
    ),
    path("club-profile/<slug:slug>/", views.club_profile, name="club_profile"),
]
