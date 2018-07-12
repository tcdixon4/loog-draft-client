from django.db import models

class Player(models.Model):
	name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    owner = models.ForeignKey(Question, on_delete=models.CASCADE)
    keeper_val = models.IntegerField(default=0)

class Team(models.Model):
    team_name = models.CharField(max_length=200)

class Draft(models.Model):
	round = models.IntegerField(default=0)
