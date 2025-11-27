from django.db import models
from django.contrib.auth.models import User

class Turma(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=255)  # <-- adiciona isso

    def __str__(self):
        return self.nome_completo


class Aluno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=255)  # <-- adicionei aqui
    idade = models.IntegerField()
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome_completo


class Disciplina(models.Model):
    nome = models.CharField(max_length=100)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.nome} ({self.turma})"


class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    nota1 = models.FloatField(null=True, blank=True)
    nota2 = models.FloatField(null=True, blank=True)
    nota3 = models.FloatField(null=True, blank=True)
    nota4 = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('aluno', 'disciplina')

    def media(self):
        notas = [n for n in [self.nota1, self.nota2, self.nota3, self.nota4] if n is not None]
        if notas:
            return sum(notas) / len(notas)
        return None

    def __str__(self):
        return f"{self.aluno} - {self.disciplina}"


class Gestor(models.Model):
    CARGO_CHOICES = [
        ('diretor', 'Diretor'),
        ('vice_diretor', 'Vice-Diretor'),
        ('secretario', 'Secretário'),
        ('coordenador', 'Coordenador'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=150)
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES)

    def __str__(self):
        return f"{self.nome_completo} ({self.get_cargo_display()})"