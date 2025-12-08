from django.db import models
from django.contrib.auth.models import User


# ------------------ TURMA ------------------
class Turma(models.Model):
    TURNO_CHOICES = [
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('noite', 'Noite'),
    ]

    nome = models.CharField(max_length=100)
    turno = models.CharField(max_length=20, choices=TURNO_CHOICES, default='manha')
    ano = models.IntegerField()

    def __str__(self):
        return f"{self.nome} - {self.get_turno_display()} ({self.ano})"


# ------------------ PROFESSOR ------------------
class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=255)
    foto = models.ImageField(upload_to="fotos/", null=True, blank=True)

    def __str__(self):
        return self.nome_completo


# ------------------ ALUNO ------------------
class Aluno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=255)
    idade = models.IntegerField()
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to="fotos/", null=True, blank=True)

    def __str__(self):
        return self.nome_completo


# ------------------ DISCIPLINA ------------------
class Disciplina(models.Model):
    nome = models.CharField(max_length=100)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nome} ({self.turma})"


# ------------------ NOTAS ------------------
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
        return sum(notas) / len(notas) if notas else None

    def __str__(self):
        return f"{self.aluno} - {self.disciplina}"


# ------------------ GESTOR ------------------
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
    foto = models.ImageField(upload_to="fotos/", null=True, blank=True)

    def __str__(self):
        return f"{self.nome_completo} ({self.get_cargo_display()})"


# ------------------ GRADE HORÁRIA ------------------
class GradeHorario(models.Model):
    turma = models.OneToOneField("Turma", on_delete=models.CASCADE)
    dados = models.JSONField(default=dict)  # tabela completa da grade

    def __str__(self):
        return f"Grade Horária - {self.turma}"
