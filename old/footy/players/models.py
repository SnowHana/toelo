from django.db import models


POSITION_TYPE = (
    ("DF", "DF"),
    ("FW", "FW"),
)


# Create your models here.
class Player(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)

    def __str__(self):
        return self.name
