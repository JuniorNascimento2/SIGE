from django import forms
from django.contrib.auth.models import User
from .models import Professor, Aluno, Disciplina, Turma, Nota, Gestor
from django.contrib.auth import authenticate


# --- LOGIN ---
class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'E-mail'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("E-mail não encontrado.")

        user = authenticate(username=user_obj.username, password=password)
        if not user:
            raise forms.ValidationError("Senha incorreta.")
        self.user = user
        return self.cleaned_data

    def get_user(self):
        return self.user


# --- PROFESSOR ---
from django import forms
from django.contrib.auth.models import User
from .models import Professor


class ProfessorForm(forms.ModelForm):
    # -------- Dados de login (User) --------
    email = forms.EmailField(label='E-mail')
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput
    )
    confirmar_senha = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput
    )

    # -------- Ajustes de labels --------
    data_nascimento = forms.DateField(
        label='Data de nascimento',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )

    class Meta:
        model = Professor
        fields = [
            # Dados pessoais
            'nome_completo',
            'cpf',
            'telefone',
            'data_nascimento',

            # Endereço
            'cep',
            'estado',
            'cidade',
            'bairro',
            'logradouro',
            'numero',
            'complemento',

            # Profissional
            'formacao',
            'especializacao',
            'area_atuacao',

        ]

    # -------- Validação --------
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('password')
        confirmar = cleaned_data.get('confirmar_senha')

        if senha and confirmar and senha != confirmar:
            self.add_error('confirmar_senha', 'As senhas não coincidem.')

        return cleaned_data



# --- ALUNO ---
class AlunoForm(forms.ModelForm):
    # ---------- DADOS DO USUÁRIO ----------
    email = forms.EmailField(label='E-mail')
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput
    )
    password_confirm = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput
    )

    # ---------- DADOS DO ALUNO ----------
    nome_completo = forms.CharField(label='Nome completo')
    cpf = forms.CharField(label='CPF', max_length=14)

    class Meta:
        model = Aluno
        fields = [
            'nome_completo',
            'cpf',
            'turma',
        ]

    # ---------- VALIDAÇÕES ----------
    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']

        if Aluno.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError('CPF já cadastrado.')

        return cpf

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'As senhas não coincidem.')

        return cleaned_data


# --- DISCIPLINA ---
class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'professor', 'turma']


# --- TURMA ---
class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['nome', 'turno', 'ano']



# --- NOTA ---
class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['nota1', 'nota2', 'nota3', 'nota4']


from django import forms
from django.contrib.auth.models import User

class EditarPerfilForm(forms.ModelForm):
    senha_atual = forms.CharField(
        label="Senha atual",
        required=False,
        widget=forms.PasswordInput
    )

    nova_senha = forms.CharField(
        label="Nova senha",
        required=False,
        widget=forms.PasswordInput
    )

    confirmar_senha = forms.CharField(
        label="Confirmar nova senha",
        required=False,
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")

        return email

    def clean(self):
        cleaned_data = super().clean()

        senha_atual = cleaned_data.get("senha_atual")
        nova_senha = cleaned_data.get("nova_senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        # Só valida senha se o usuário tentou alterar
        if senha_atual or nova_senha or confirmar_senha:

            if not senha_atual:
                raise forms.ValidationError("Informe a senha atual.")

            if not self.instance.check_password(senha_atual):
                raise forms.ValidationError("Senha atual incorreta.")

            if not nova_senha or not confirmar_senha:
                raise forms.ValidationError("Preencha a nova senha e a confirmação.")

            if nova_senha != confirmar_senha:
                raise forms.ValidationError("As senhas não coincidem.")

        return cleaned_data





# --- EDITAR PERFIL PROFESSOR ---
class EditarPerfilProfessorForm(forms.ModelForm):
    nome_completo = forms.CharField(label='Nome completo')
    nova_senha = forms.CharField(
        label='Nova Senha',
        required=False,
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['nome_completo', 'email']


# --- EDITAR PERFIL ALUNO ---
class EditarPerfilAlunoForm(forms.ModelForm):
    nome_completo = forms.CharField(label='Nome completo')
    nova_senha = forms.CharField(
        label='Nova Senha',
        required=False,
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['nome_completo', 'email']


from django import forms
from django.contrib.auth.models import User
from .models import Gestor

from django import forms
from django.contrib.auth.models import User
from .models import Gestor

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from .models import Gestor

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from .models import Gestor

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Gestor


from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Gestor

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash

from .models import Gestor


class GestorForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="E-mail"
    )

    senha = forms.CharField(
        required=False,  # 🔥 NÃO OBRIGATÓRIA NA EDIÇÃO
        label="Senha",
        widget=forms.PasswordInput(render_value=False)
    )

    senha_confirmacao = forms.CharField(
        required=False,  # 🔥 NÃO OBRIGATÓRIA NA EDIÇÃO
        label="Confirmar senha",
        widget=forms.PasswordInput(render_value=False)
    )

    class Meta:
        model = Gestor
        fields = [
            'nome_completo',
            'cpf',
            'data_nascimento',
            'telefone',
            'cep',
            'uf',
            'cidade',
            'endereco',
            'cargo',
            'foto',
        ]

        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # 🔒 TODOS OBRIGATÓRIOS
        for field in self.fields.values():
            field.required = True

        # 📸 FOTO NÃO OBRIGATÓRIA
        self.fields['foto'].required = False

        # 🔑 SENHA SÓ É OBRIGATÓRIA NO CADASTRO
        if self.instance.pk:
            self.fields['senha'].required = False
            self.fields['senha_confirmacao'].required = False
        else:
            self.fields['senha'].required = True
            self.fields['senha_confirmacao'].required = True

        # 📧 carregar e-mail do usuário na edição
        if self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    # =========================
    # VALIDAÇÕES INDIVIDUAIS
    # =========================

    def clean_email(self):
        email = self.cleaned_data.get('email')

        qs = User.objects.filter(email=email)

        if self.instance.pk and hasattr(self.instance, 'user'):
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise ValidationError("Este e-mail já está em uso.")

        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')

        qs = Gestor.objects.filter(cpf=cpf)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Este CPF já está cadastrado.")

        return cpf

    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        cep_numeros = cep.replace('-', '')

        if len(cep_numeros) != 8 or not cep_numeros.isdigit():
            raise ValidationError("Informe um CEP válido.")

        return cep

    # =========================
    # VALIDAÇÃO DE SENHA
    # =========================

    def clean(self):
        cleaned_data = super().clean()

        senha = cleaned_data.get('senha')
        senha_confirmacao = cleaned_data.get('senha_confirmacao')

        # 👉 não quer trocar senha → OK
        if not senha and not senha_confirmacao:
            return cleaned_data

        # 👉 digitou um → precisa dos dois
        if not senha or not senha_confirmacao:
            raise ValidationError("Informe a senha e a confirmação.")

        if senha != senha_confirmacao:
            raise ValidationError("As senhas não coincidem.")

        validate_password(senha)

        return cleaned_data

    # =========================
    # SAVE
    # =========================

    def save(self, commit=True):
        gestor = super().save(commit=False)

        email = self.cleaned_data.get('email')
        senha = self.cleaned_data.get('senha')

        if gestor.user:
            gestor.user.email = email
            gestor.user.username = email

            # 🔥 só troca senha se digitou
            if senha:
                gestor.user.set_password(senha)

            if commit:
                gestor.user.save()

                if self.request and senha:
                    update_session_auth_hash(self.request, gestor.user)

        if commit:
            gestor.save()

        return gestor


class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'professor']

