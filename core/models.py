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

    # ================= DADOS PESSOAIS =================
    nome_completo = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)

    # ================= ENDEREÇO =================
    cep = models.CharField(max_length=9, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=10, blank=True)
    complemento = models.CharField(max_length=100, blank=True)

    # ================= DADOS PROFISSIONAIS =================
    formacao = models.CharField(max_length=255, blank=True)
    especializacao = models.CharField(max_length=255, blank=True)
    area_atuacao = models.CharField(max_length=255, blank=True)

    foto = models.ImageField(upload_to="fotos/", null=True, blank=True)

    def __str__(self):
        return self.nome_completo


# ------------------ ALUNO ------------------
# ------------------ ALUNO ------------------
class Aluno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Dados pessoais
    nome_completo = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    data_nascimento = models.DateField(null=True, blank=False)

    NATURALIDADE_CHOICES = [
        ('brasileiro', 'Brasileiro(a)'),
        ('estrangeiro', 'Estrangeiro(a)'),
    ]
    naturalidade = models.CharField(
        max_length=20,
        choices=NATURALIDADE_CHOICES,
        blank=True
    )

    filiacao_1 = models.CharField(max_length=255, blank=False)
    filiacao_2 = models.CharField(max_length=255, blank=True)

    necessidade_especial = models.BooleanField(default=False)
    descricao_necessidade = models.TextField(blank=True)

    # Endereço
    cep = models.CharField(max_length=9, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=10, blank=True)

    # Alocação
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
from django.db import models
from django.contrib.auth.models import User


from django.db import models
from django.contrib.auth.models import User


from django.db import models
from django.contrib.auth.models import User


class Gestor(models.Model):

    # ------------------ CARGOS ------------------
    CARGO_CHOICES = [
        ('diretor', 'Diretor'),
        ('vice_diretor', 'Vice-Diretor'),
        ('secretario', 'Secretário'),
        ('coordenador', 'Coordenador'),
    ]

    # ------------------ UFs ------------------
    UF_CHOICES = [
        ("AC", "AC"), ("AL", "AL"), ("AP", "AP"), ("AM", "AM"),
        ("BA", "BA"), ("CE", "CE"), ("DF", "DF"), ("ES", "ES"),
        ("GO", "GO"), ("MA", "MA"), ("MT", "MT"), ("MS", "MS"),
        ("MG", "MG"), ("PA", "PA"), ("PB", "PB"), ("PR", "PR"),
        ("PE", "PE"), ("PI", "PI"), ("RJ", "RJ"), ("RN", "RN"),
        ("RS", "RS"), ("RO", "RO"), ("RR", "RR"), ("SC", "SC"),
        ("SP", "SP"), ("SE", "SE"), ("TO", "TO"),
    ]

    # ------------------ RELAÇÃO COM USUÁRIO ------------------
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # ------------------ DADOS PESSOAIS ------------------
    nome_completo = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    telefone = models.CharField(max_length=20)
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES)

    # ------------------ ENDEREÇO ------------------
    cep = models.CharField(max_length=9)  # 00000-000
    uf = models.CharField(max_length=2, choices=UF_CHOICES)
    cidade = models.CharField(max_length=100)
    endereco = models.CharField(max_length=255)

    # ------------------ FOTO ------------------
    foto = models.ImageField(upload_to="fotos/", null=True, blank=True)

    def __str__(self):
        return f"{self.nome_completo} ({self.get_cargo_display()})"


# ------------------ GRADE HORÁRIA ------------------
class GradeHorario(models.Model):
    turma = models.OneToOneField("Turma", on_delete=models.CASCADE)
    dados = models.JSONField(default=dict)  # tabela completa da grade

    def __str__(self):
        return f"Grade Horária - {self.turma}"


