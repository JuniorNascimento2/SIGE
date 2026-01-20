from django import forms
from django.contrib.auth.models import User
from .models import Professor, Aluno, Disciplina, Turma, Nota, Gestor
from django.contrib.auth import authenticate
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash


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


from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from .models import Professor


class ProfessorForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="E-mail"
    )

    senha = forms.CharField(
        required=False,
        label="Senha",
        widget=forms.PasswordInput(render_value=False)
    )

    senha_confirmacao = forms.CharField(
        required=False,
        label="Confirmar senha",
        widget=forms.PasswordInput(render_value=False)
    )

    class Meta:
        model = Professor
        fields = [
            'nome_completo',
            'cpf',
            'data_nascimento',
            'telefone',
            'cep',
            'estado',
            'cidade',
            'bairro',
            'logradouro',
            'numero',
            'complemento',
            'formacao',
            'especializacao',
            'area_atuacao',
            'foto',
        ]

        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00'}),
            'cep': forms.TextInput(attrs={'placeholder': '00000-000'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # 🔒 Campos obrigatórios
        campos_obrigatorios = [
            'nome_completo', 'cpf', 'email', 'telefone',
            'cep', 'estado', 'cidade', 'logradouro', 'numero'
        ]
        
        for campo in campos_obrigatorios:
            if campo in self.fields:
                self.fields[campo].required = True

        # 📸 Campos opcionais
        campos_opcionais = [
            'foto', 'data_nascimento', 'bairro', 'complemento',
            'formacao', 'especializacao', 'area_atuacao'
        ]
        
        for campo in campos_opcionais:
            if campo in self.fields:
                self.fields[campo].required = False

        # 🔑 Senha só é obrigatória no cadastro
        if self.instance.pk:
            self.fields['senha'].required = False
            self.fields['senha_confirmacao'].required = False
        else:
            self.fields['senha'].required = True
            self.fields['senha_confirmacao'].required = True

        # 📧 Carregar e-mail do usuário na edição
        if self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    # =========================
    # VALIDAÇÕES INDIVIDUAIS
    # =========================

    def clean_email(self):
        email = self.cleaned_data.get('email')

        qs = User.objects.filter(email=email)

        if self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise ValidationError("Este e-mail já está em uso.")

        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')

        qs = Professor.objects.filter(cpf=cpf)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Este CPF já está cadastrado.")

        return cpf

    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        if not cep:
            return cep
            
        cep_numeros = cep.replace('-', '').replace('.', '')

        if len(cep_numeros) != 8 or not cep_numeros.isdigit():
            raise ValidationError("Informe um CEP válido (8 dígitos).")

        return cep

    # =========================
    # VALIDAÇÃO DE SENHA
    # =========================

    def clean(self):
        cleaned_data = super().clean()

        senha = cleaned_data.get('senha')
        senha_confirmacao = cleaned_data.get('senha_confirmacao')

        # 👉 Não quer trocar senha → OK
        if not senha and not senha_confirmacao:
            return cleaned_data

        # 👉 Digitou um → precisa dos dois
        if not senha or not senha_confirmacao:
            raise ValidationError("Informe a senha e a confirmação.")

        if senha != senha_confirmacao:
            raise ValidationError("As senhas não coincidem.")

        # ✅ Validar tamanho mínimo
        if len(senha) < 6:
            raise ValidationError("A senha deve ter pelo menos 6 caracteres.")

        return cleaned_data

    # =========================
    # SAVE
    # =========================

    def save(self, commit=True):
        professor = super().save(commit=False)

        email = self.cleaned_data.get('email')
        senha = self.cleaned_data.get('senha')

        # 🆕 CRIAÇÃO: criar o User
        if not professor.user_id:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=senha
            )
            professor.user = user

        # ✏️ EDIÇÃO: atualizar o User existente
        else:
            professor.user.email = email
            professor.user.username = email

            # 🔥 Só troca senha se digitou
            if senha:
                professor.user.set_password(senha)

                # Mantém o usuário logado após trocar senha
                if commit and self.request:
                    update_session_auth_hash(self.request, professor.user)

            if commit:
                professor.user.save()

        if commit:
            professor.save()

        return professor


# --- ALUNO ---
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from .models import Aluno, Turma


class AlunoForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="E-mail"
    )

    senha = forms.CharField(
        required=False,
        label="Senha",
        widget=forms.PasswordInput(render_value=False)
    )

    senha_confirmacao = forms.CharField(
        required=False,
        label="Confirmar senha",
        widget=forms.PasswordInput(render_value=False)
    )

    class Meta:
        model = Aluno
        fields = [
            'nome_completo',
            'cpf',
            'data_nascimento',
            'telefone',
            'naturalidade',
            'filiacao_1',
            'filiacao_2',
            'necessidade_especial',
            'descricao_necessidade',
            'cep',
            'estado',
            'cidade',
            'bairro',
            'logradouro',
            'numero',
            'turma',
            'foto',
        ]

        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00'}),
            'cep': forms.TextInput(attrs={'placeholder': '00000-000'}),
            'descricao_necessidade': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # 🔒 Campos obrigatórios
        campos_obrigatorios = [
            'nome_completo', 'cpf', 'email', 'data_nascimento', 
            'naturalidade', 'filiacao_1',
            'cep', 'estado', 'cidade', 'logradouro', 'numero', 'turma'
        ]
        
        for campo in campos_obrigatorios:
            if campo in self.fields:
                self.fields[campo].required = True

        # 📸 Campos opcionais
        campos_opcionais = [
            'foto', 'filiacao_2', 'bairro', 'descricao_necessidade', 'telefone'
        ]
        
        for campo in campos_opcionais:
            if campo in self.fields:
                self.fields[campo].required = False

        # 🔑 Senha só é obrigatória no cadastro
        if self.instance.pk:
            self.fields['senha'].required = False
            self.fields['senha_confirmacao'].required = False
        else:
            self.fields['senha'].required = True
            self.fields['senha_confirmacao'].required = True

        # 📧 Carregar e-mail do usuário na edição
        if self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

        # 📝 Descrição NE só obrigatória se marcar necessidade_especial
        # Isso será validado no clean()
        self.fields['descricao_necessidade'].required = False

    # =========================
    # VALIDAÇÕES INDIVIDUAIS
    # =========================

    def clean_email(self):
        email = self.cleaned_data.get('email')

        qs = User.objects.filter(email=email)

        if self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            qs = qs.exclude(pk=self.instance.user.pk)

        if qs.exists():
            raise ValidationError("Este e-mail já está em uso.")

        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')

        qs = Aluno.objects.filter(cpf=cpf)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Este CPF já está cadastrado.")

        return cpf

    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        if not cep:
            return cep
            
        cep_numeros = cep.replace('-', '').replace('.', '')

        if len(cep_numeros) != 8 or not cep_numeros.isdigit():
            raise ValidationError("Informe um CEP válido (8 dígitos).")

        return cep

    # =========================
    # VALIDAÇÃO GERAL
    # =========================

    def clean(self):
        cleaned_data = super().clean()

        senha = cleaned_data.get('senha')
        senha_confirmacao = cleaned_data.get('senha_confirmacao')
        necessidade_especial = cleaned_data.get('necessidade_especial')
        descricao_necessidade = cleaned_data.get('descricao_necessidade')

        # Validação de senha
        if not senha and not senha_confirmacao:
            pass  # OK, não quer trocar senha
        else:
            if not senha or not senha_confirmacao:
                raise ValidationError("Informe a senha e a confirmação.")

            if senha != senha_confirmacao:
                raise ValidationError("As senhas não coincidem.")

            if len(senha) < 6:
                raise ValidationError("A senha deve ter pelo menos 6 caracteres.")

        # Validação de necessidade especial
        if necessidade_especial and not descricao_necessidade:
            raise ValidationError(
                "Por favor, descreva a necessidade especial do aluno."
            )

        return cleaned_data

    # =========================
    # SAVE
    # =========================

    def save(self, commit=True):
        aluno = super().save(commit=False)

        email = self.cleaned_data.get('email')
        senha = self.cleaned_data.get('senha')

        # 🆕 CRIAÇÃO: criar o User
        if not aluno.user_id:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=senha
            )
            aluno.user = user

        # ✏️ EDIÇÃO: atualizar o User existente
        else:
            aluno.user.email = email
            aluno.user.username = email

            # 🔥 Só troca senha se digitou
            if senha:
                aluno.user.set_password(senha)

                # Mantém o usuário logado após trocar senha
                if commit and self.request:
                    update_session_auth_hash(self.request, aluno.user)

            if commit:
                aluno.user.save()

        if commit:
            aluno.save()

        return aluno

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







from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from .models import Gestor


class GestorForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="E-mail"
    )

    senha = forms.CharField(
        required=False,
        label="Senha",
        widget=forms.PasswordInput(render_value=False)
    )

    senha_confirmacao = forms.CharField(
        required=False,
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
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00'}),
            'cep': forms.TextInput(attrs={'placeholder': '00000-000'}),
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

        if self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
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
        cep_numeros = cep.replace('-', '').replace('.', '')

        if len(cep_numeros) != 8 or not cep_numeros.isdigit():
            raise ValidationError("Informe um CEP válido (8 dígitos).")

        return cep

    # =========================
    # VALIDAÇÃO DE SENHA
    # =========================

    def clean(self):
        cleaned_data = super().clean()

        senha = cleaned_data.get('senha')
        senha_confirmacao = cleaned_data.get('senha_confirmacao')

        # 👉 edição sem trocar senha → OK
        if not senha and not senha_confirmacao:
            return cleaned_data

        # 👉 digitou um → precisa dos dois
        if not senha or not senha_confirmacao:
            raise ValidationError("Informe a senha e a confirmação.")

        if senha != senha_confirmacao:
            raise ValidationError("As senhas não coincidem.")

        # ✅ opcional: validar força da senha
        if len(senha) < 6:
            raise ValidationError("A senha deve ter pelo menos 6 caracteres.")

        return cleaned_data

    # =========================
    # SAVE
    # =========================

    def save(self, commit=True):
        gestor = super().save(commit=False)

        email = self.cleaned_data.get('email')
        senha = self.cleaned_data.get('senha')

        # 🆕 CRIAÇÃO: criar o User
        if not gestor.user_id:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=senha  # ✅ senha obrigatória no cadastro
            )
            gestor.user = user

        # ✏️ EDIÇÃO: atualizar o User existente
        else:
            gestor.user.email = email
            gestor.user.username = email

            # 🔥 só troca senha se digitou
            if senha:
                gestor.user.set_password(senha)

                # mantém o usuário logado após trocar senha
                if commit and self.request:
                    update_session_auth_hash(self.request, gestor.user)

            if commit:
                gestor.user.save()

        if commit:
            gestor.save()

        return gestor


class DisciplinaForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = ['nome', 'professor']

