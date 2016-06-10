from django.db import models


class Quiz(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=300)

    def __str__(self):
        return self.name + " - " + self.description


class Question(models.Model):
    quiz = models.ForeignKey(Quiz)
    text = models.CharField(max_length=400)

    def __str__(self):
        return self.text

    def quiz_name(self): # you can use question.quiz.name everywhere, even templates
        return self.quiz.name


class Option(models.Model):
    question = models.ForeignKey(Question)
    text = models.CharField(max_length=200)
    scor = models.IntegerField()

    def __str__(self):
        return self.text
