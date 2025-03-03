from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Club(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True)
    club_code = models.CharField(max_length=100, default="CR7")
    country = models.CharFiled(max_length=100, blank=True, null=True, default=None)
    level = models.PositiveIntegerField(blank=True, null=True, default=None)

    # domestic_competition_id = models.
    elo = models.FloatField(default=1000)
    squad_size = models.PositiveIntegerField(blank=True, null=True, default=1000)
    avg_age = models.PositiveIntegerField(blank=True, null=True, default=1000)
    total_market_value = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True, default=1000
    )
    # Store alternative names
    other_names = models.JSONField(blank=True, null=True, default=None)

    # elo =
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Automatically generate slug from the name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("club_detail", args=[self.slug])

    def get_all_names(self):
        """Return a list of all possible names of a club, ie) FC Barcelona, Futbol Clube de Barcelona etc..."""
        if self.other_names:
            return [self.name] + self.other_names
        else:
            return [self.name]


class Player(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, unique=True)
    age = models.IntegerField()
    born = models.IntegerField()
    nation = models.CharField(max_length=100)
    position = models.CharField(max_length=10)
    club = models.ForeignKey(Club, related_name="player", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.name} : {self.club}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Generate slug from name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("player_detail", args=[self.slug])


class PlayerStat(models.Model):
    player = models.OneToOneField(
        Player,
        on_delete=models.CASCADE,
        related_name="playerstats",
        help_text="Player associated with this player stat.",
    )
    # slug = models.SlugField(max_length=255, unique=True)
    competition = models.CharField(max_length=100)
    mp = models.IntegerField()  # Matches played
    starts = models.IntegerField()
    minutes = models.IntegerField()
    nineties = models.FloatField()  # 90s
    goals = models.IntegerField()
    assists = models.IntegerField()
    goals_assists = models.IntegerField()  # G+A
    goals_minus_pens = models.IntegerField()  # G-PK
    penalties = models.IntegerField()  # PK
    penalties_attempted = models.IntegerField()  # PKatt
    yellow_cards = models.IntegerField()  # CrdY
    red_cards = models.IntegerField()  # CrdR
    xg = models.FloatField()  # Expected goals
    npxg = models.FloatField()  # Non-penalty expected goals
    xag = models.FloatField()  # Expected assists
    npxg_plus_xag = models.FloatField()  # Non-penalty xG + xAG
    prog_carries = models.IntegerField()  # Progressive carries
    prog_passes = models.IntegerField()  # Progressive passes
    prog_runs = models.IntegerField()  # Progressive runs
    goals_per_90 = models.FloatField()  # Gls-90
    assists_per_90 = models.FloatField()  # Ast-90
    goals_assists_per_90 = models.FloatField()  # G+A-90
    goals_minus_pens_per_90 = models.FloatField()  # G-PK-90
    goals_assists_minus_pens = models.FloatField()  # G+A-PK
    xg_per_90 = models.FloatField()  # xG-90
    xag_per_90 = models.FloatField()  # xAG-90
    xg_plus_xag = models.FloatField()  # xG+xAG
    npxg_per_90 = models.FloatField()  # npxG-90
    npxg_plus_xag_per_90 = models.FloatField()  # npxG+xAG-90

    class Meta:
        ordering = [
            "player",
        ]

    def __str__(self):
        return f"Stats for {self.player}"

    def save(self, *args, **kwargs):
        # if not self.slug:
        #     self.slug = slugify(self.name)  # Generate slug from name
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("player_stats_detail", args=[self.player.slug])
