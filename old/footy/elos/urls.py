from django.urls import path
from . import views


urlpatterns = [
    path("", views.elos_home, name="elos_home"),
    # path("players-all/", views.players_all, name="players_all"),
    # path("player-stats/<slug:slug>/", views.player_stats, name="player_stats"),
    # path(
    #     "player-stats/<slug:slug>/graph/", views.generate_graph, name="generate_graph"
    # ),
]
