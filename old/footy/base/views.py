from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Player, Club, PlayerStat
from django.db.models import Avg
import plotly.graph_objs as go

# matplotlib.use("Agg")  # Ensure non-GUI backend for rendering on macOS
# Create your views here.


def home(request) -> HttpResponse:
    context = {}
    # return render(request, "base/home.html", context)
    return render(request, "base/home.html", context)


def players_all(request) -> HttpResponse:

    players = Player.objects.all()[:50]

    context = {"players": players}

    # clubs = Club.objects.all().filter()

    return render(
        request,
        "base/players_all.html",
        context,
    )


def club_profile(request, slug):
    club = get_object_or_404(Club, slug=slug)

    # Get fields
    fields = [
        (field.verbose_name, field.value_from_object(club))
        for field in Club._meta.fields
        if field.name not in ["id"]
    ]

    context = {"club": club, "fields": fields}
    return render(request, "base/club_profile.html", context)


def player_stats(request, slug):
    player_stats = get_object_or_404(
        PlayerStat,
        player__slug=slug,
    )

    # Get fileds of Player Stats value

    fields = [
        (field.verbose_name, field.value_from_object(player_stats))
        for field in PlayerStat._meta.fields
        if field.name not in ["id", "player", "competition"]
    ]

    context = {"player_stats": player_stats, "fields": fields}
    return render(request, "base/player_stats.html", context)


def generate_graph(request, slug):
    feature = request.GET.get("feature", None)  # Get the feature from the AJAX request

    if not feature:
        return JsonResponse({"error": "Feature is required"}, status=400)

    # Fetch the player's stats and necessary attributes using get_object_or_404
    player_stat = get_object_or_404(PlayerStat, player__slug=slug)
    player = player_stat.player
    feature_field = feature.lower().replace(" ", "_")
    player_value = getattr(player_stat, feature_field, None)

    if player_value is None:
        return JsonResponse({"error": "Feature not found for player"}, status=400)

    # Calculate the averages based on competition, age, position, and nationality
    league_avg = PlayerStat.objects.filter(
        competition=player_stat.competition
    ).aggregate(avg_value=Avg(feature_field))["avg_value"]

    age_group_avg = PlayerStat.objects.filter(player__age=player.age).aggregate(
        avg_value=Avg(feature_field)
    )["avg_value"]

    position_avg = PlayerStat.objects.filter(
        player__position=player.position
    ).aggregate(avg_value=Avg(feature_field))["avg_value"]

    nationality_avg = PlayerStat.objects.filter(player__nation=player.nation).aggregate(
        avg_value=Avg(feature_field)
    )["avg_value"]

    # Prepare data for the graph
    categories = [
        "Player",
        "League Avg",
        "Age Group Avg",
        "Position Avg",
        "Nationality Avg",
    ]
    values = [player_value, league_avg, age_group_avg, position_avg, nationality_avg]
    # Create the Plotly bar graph
    fig = go.Figure()

    # Add bars with different colors
    colors = ["black", "gray", "gray", "gray", "gray"]
    for i, (category, value) in enumerate(zip(categories, values)):
        fig.add_trace(
            go.Bar(
                x=[category],
                y=[value],
                name=category,
                marker_color=colors[i],
                text=[f"{value:.2f}"],  # Display value on hover
                textposition="auto",  # Position text labels on top of bars
                width=0.5,
            )
        )

    # Update layout for better interaction
    fig.update_layout(
        title=f"{player.name} - {feature} Comparison",
        xaxis_title="Category",
        yaxis_title="Value",
        barmode="group",
        hovermode="x unified",
    )

    # Convert the figure to a PNG image and encode it as base64
    graph_json = fig.to_json()
    return JsonResponse({"graph_json": graph_json})
    # # Convert the graph to a PNG image and encode it as base64
    # buffer = io.BytesIO()
    # plt.savefig(buffer, format="png")
    # buffer.seek(0)
    # graph_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    # buffer.close()

    # return JsonResponse({"graph": graph_base64})


# class (DetailView):
#     model = Player
#     template_name = "player_detail.html"
#     context_object_name = "player"


# class TeamDetailView(DetailView):
#     model = Team
#     template_name = "team_detail.html"
#     context_object_name = "team"


# class PlayerStatDetailView(DetailView):
#     model = PlayerStat
#     template_name = "player_stats_detail.html"
#     context_object_name = "player_stats"
