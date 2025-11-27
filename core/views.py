from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Professor, Aluno, Disciplina, Turma, Nota, Gestor
from .forms import (
    LoginForm, ProfessorForm, AlunoForm, DisciplinaForm, TurmaForm,
    NotaForm, EditarPerfilForm, EditarPerfilProfessorForm, EditarPerfilAlunoForm, GestorForm
)

# -------------------- LOGIN / LOGOUT --------------------
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('painel_super')
        elif hasattr(request.user, 'professor'):
            return redirect('painel_professor')
        elif hasattr(request.user, 'aluno'):
            return redirect('painel_aluno')
        elif hasattr(request.user, 'gestor'):
            return redirect('painel_gestor')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('painel_super')
            elif hasattr(user, 'professor'):
                return redirect('painel_professor')
            elif hasattr(user, 'aluno'):
                return redirect('painel_aluno')
            elif hasattr(user, 'gestor'):
                return redirect('painel_gestor')  # <- adicionado
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('login')


# -------------------- SUPERUSUÁRIO --------------------
def is_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(is_superuser)
def painel_super(request):
    return render(request, 'core/painel_super.html', {
        'usuario': request.user,
        'total_professores': Professor.objects.count(),
        'total_alunos': Aluno.objects.count(),
        'total_turmas': Turma.objects.count(),
        'total_disciplinas': Disciplina.objects.count(),
    })



@login_required
@user_passes_test(is_superuser)
def editar_perfil(request):
    user = request.user
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=user)
        if form.is_valid():
            # Salva dados normais (nome, email) sem alterar a senha
            user = form.save(commit=False)
            user.save()
            
            # Só altera a senha se algo foi digitado
            nova_senha = form.cleaned_data.get('nova_senha')
            if nova_senha:
                user.set_password(nova_senha)
                user.save()
                update_session_auth_hash(request, user)
            
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect('painel_super')
    else:
        form = EditarPerfilForm(instance=user)
    return render(request, 'core/editar_perfil.html', {'form': form})


# -------------------- PROFESSORES --------------------
@login_required
@user_passes_test(is_superuser)
def listar_professores(request):
    query = request.GET.get('q', '')
    professores = Professor.objects.filter(nome_completo__icontains=query) if query else Professor.objects.all()
    return render(request, 'core/listar_professores.html', {'professores': professores, 'query': query})


@login_required
@user_passes_test(is_superuser)
def cadastrar_professor(request):
    erro = None
    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha', '').strip()

        if not nome_completo or not email or not senha:
            erro = 'Preencha todos os campos obrigatórios.'
        elif User.objects.filter(email=email).exists():
            erro = 'Já existe um usuário com este e-mail.'
        else:
            user = User.objects.create_user(username=email, email=email, password=senha)
            Professor.objects.create(user=user, nome_completo=nome_completo)
            messages.success(request, f'Professor {nome_completo} cadastrado com sucesso!')
            return redirect('listar_professores')

    return render(request, 'core/cadastrar_professor.html', {'erro': erro})


@login_required
@user_passes_test(is_superuser)
def editar_professor(request, professor_id):
    professor = get_object_or_404(Professor, id=professor_id)
    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha', '').strip()

        if not nome_completo or not email:
            messages.error(request, 'Preencha os campos obrigatórios.')
        else:
            user = professor.user
            user.email = email
            user.username = email
            if senha:
                user.set_password(senha)
            user.save()
            professor.nome_completo = nome_completo
            professor.save()
            messages.success(request, 'Professor atualizado com sucesso!')
            return redirect('listar_professores')

    return render(request, 'core/editar_professor.html', {'professor': professor})


@login_required
@user_passes_test(is_superuser)
def excluir_professor(request, professor_id):
    professor = get_object_or_404(Professor, id=professor_id)
    professor.user.delete()
    professor.delete()
    messages.success(request, 'Professor removido.')
    return redirect('listar_professores')

# ---- GESTOR (Painel da Gestão Escolar) ----
@login_required
def painel_gestor(request):
    if not hasattr(request.user, 'gestor'):
        return redirect('login')

    gestor = request.user.gestor
    cargo = gestor.cargo

    total_professores = Professor.objects.count()
    total_alunos = Aluno.objects.count()
    total_turmas = Turma.objects.count()
    total_disciplinas = Disciplina.objects.count()

    return render(request, 'core/painel_gestor.html', {
        'gestor': gestor,
        'cargo': cargo,
        'total_professores': total_professores,
        'total_alunos': total_alunos,
        'total_turmas': total_turmas,
        'total_disciplinas': total_disciplinas,
    })

# ---- GESTORES ----
@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'gestor') and u.gestor.cargo in ['diretor', 'vice_diretor']))
def cadastrar_gestor(request):
    if request.method == 'POST':
        form = GestorForm(request.POST)
        if form.is_valid():
            nome_completo = form.cleaned_data['nome_completo']
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']
            cargo = form.cleaned_data['cargo']

            # Cria user e gestor
            user = User.objects.create_user(username=email, email=email, password=senha)
            Gestor.objects.create(user=user, nome_completo=nome_completo, cargo=cargo)
            messages.success(request, f"{cargo.title()} {nome_completo} cadastrado com sucesso!")
            return redirect('listar_gestores')
    else:
        form = GestorForm()

    return render(request, 'core/cadastrar_gestor.html', {'form': form})

# ---- GESTOR (Painel da Gestão Escolar) ----
@login_required
def painel_gestor(request):
    # Pega o gestor logado
    if not hasattr(request.user, 'gestor'):
        messages.error(request, "Você não é um gestor.")
        return redirect('login')

    gestor = request.user.gestor
    cargo = gestor.cargo

    total_professores = Professor.objects.count()
    total_alunos = Aluno.objects.count()
    total_turmas = Turma.objects.count()
    total_disciplinas = Disciplina.objects.count()

    return render(request, 'core/painel_gestor.html', {
        'gestor': gestor,
        'cargo': cargo,
        'total_professores': total_professores,
        'total_alunos': total_alunos,
        'total_turmas': total_turmas,
        'total_disciplinas': total_disciplinas,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or hasattr(u, 'gestor'))
def listar_gestores(request):
    gestores = Gestor.objects.select_related('user').all()
    return render(request, 'core/listar_gestores.html', {'gestores': gestores})


@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'gestor') and u.gestor.cargo in ['diretor', 'vice_diretor']))
def excluir_gestor(request, gestor_id):
    gestor = get_object_or_404(Gestor, id=gestor_id)
    gestor.user.delete()
    gestor.delete()
    messages.success(request, 'Gestor excluído com sucesso.')
    return redirect('listar_gestores')

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import GestorForm
from .models import Gestor

@login_required
@login_required
def editar_gestor(request, gestor_id):
    gestor = get_object_or_404(Gestor, id=gestor_id)
    user = gestor.user

    # Permissão: superusuário ou o próprio gestor
    if not (request.user.is_superuser or (hasattr(request.user, 'gestor') and request.user.gestor == gestor)):
        messages.error(request, "Você não tem permissão para editar este gestor.")
        return redirect('painel_gestor')

    if request.method == 'POST':
        form = GestorForm(request.POST, instance=gestor, request=request)  # passa request
        if form.is_valid():
            form.save()
            messages.success(request, 'Gestor atualizado com sucesso!')
            return redirect('painel_gestor')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = GestorForm(instance=gestor, initial={'email': user.email})

    return render(request, 'core/editar_gestor.html', {'form': form, 'gestor': gestor})



# -------------------- ALUNOS --------------------
@login_required
@user_passes_test(lambda u: u.is_superuser or hasattr(u, 'gestor'))
def listar_alunos(request):
    query = request.GET.get('q', '')
    alunos = Aluno.objects.filter(nome_completo__icontains=query) if query else Aluno.objects.all()
    return render(request, 'core/listar_alunos.html', {'alunos': alunos, 'query': query})


@login_required
@user_passes_test(is_superuser)
def cadastrar_aluno(request):
    erro = None
    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo', '').strip()
        idade = request.POST.get('idade', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha', '').strip()
        turma_id = request.POST.get('turma')

        if not nome_completo or not idade or not email or not senha or not turma_id:
            erro = 'Preencha todos os campos obrigatórios.'
        elif User.objects.filter(email=email).exists():
            erro = 'Já existe um usuário com este e-mail.'
        else:
            user = User.objects.create_user(username=email, email=email, password=senha)
            turma = get_object_or_404(Turma, id=turma_id)
            Aluno.objects.create(user=user, nome_completo=nome_completo, idade=idade, turma=turma)
            messages.success(request, f'Aluno {nome_completo} cadastrado com sucesso!')
            return redirect('listar_alunos')

    turmas = Turma.objects.all()
    return render(request, 'core/cadastrar_aluno.html', {'turmas': turmas, 'erro': erro})


@login_required
@user_passes_test(is_superuser)
def editar_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo', '').strip()
        idade = request.POST.get('idade', '').strip()
        email = request.POST.get('email', '').strip()
        turma_id = request.POST.get('turma')
        senha = request.POST.get('senha', '').strip()

        if not nome_completo or not idade or not email or not turma_id:
            messages.error(request, 'Preencha os campos obrigatórios.')
        else:
            user = aluno.user
            user.email = email
            user.username = email
            if senha:
                user.set_password(senha)
            user.save()

            aluno.nome_completo = nome_completo
            aluno.idade = idade
            aluno.turma = get_object_or_404(Turma, id=turma_id)
            aluno.save()
            messages.success(request, 'Aluno atualizado com sucesso!')
            return redirect('listar_alunos')

    turmas = Turma.objects.all()
    return render(request, 'core/editar_aluno.html', {'aluno': aluno, 'turmas': turmas})


@login_required
@user_passes_test(is_superuser)
def excluir_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    aluno.user.delete()
    aluno.delete()
    messages.success(request, 'Aluno removido.')
    return redirect('listar_alunos')




# -------------------- PERFIL ALUNO --------------------
@login_required
def editar_perfil_aluno(request):
    if not hasattr(request.user, 'aluno'):
        return redirect('login')

    aluno = request.user.aluno
    user = request.user

    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo', '').strip()
        email = request.POST.get('email', '').strip()
        nova_senha = request.POST.get('nova_senha', '').strip()

        if not nome_completo or not email:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
        else:
            aluno.nome_completo = nome_completo
            aluno.save()

            user.email = email
            user.username = email
            if nova_senha:
                user.set_password(nova_senha)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('painel_aluno')

    return render(request, 'core/editar_perfil_aluno.html', {'aluno': aluno})


# -------------------- DISCIPLINAS, TURMAS E NOTAS --------------------
# (mantém as lógicas originais do seu código, já estavam certas)


#Disciplinas






@login_required
def editar_disciplina(request, disciplina_id):
    if not request.user.is_superuser:
        return redirect('login')

    disciplina = get_object_or_404(Disciplina, id=disciplina_id)

    if request.method == 'POST':
        disciplina.nome = request.POST['nome']
        disciplina.professor = get_object_or_404(Professor, id=request.POST['professor'])
        disciplina.save()

        # redireciona direto para as disciplinas dessa turma
        return redirect('listar_disciplinas_turma', turma_id=disciplina.turma.id)

    professores = Professor.objects.all()

    return render(request, 'core/editar_disciplina.html', {
        'disciplina': disciplina,
        'professores': professores,
    })





@login_required
def excluir_disciplina(request, disciplina_id):
    disciplina = get_object_or_404(Disciplina, id=disciplina_id)
    turma_id = disciplina.turma.id  # salva antes de deletar

    disciplina.delete()
    messages.success(request, "Disciplina excluída com sucesso!")

    # 🔥 volta para a listagem de disciplinas da turma
    return redirect("listar_disciplinas_turma", turma_id=turma_id)

#Turma

@login_required
def listar_turmas(request):
    if not request.user.is_superuser:
        return redirect('login')

    query = request.GET.get('q', '')
    if query:
        turmas = Turma.objects.filter(nome__icontains=query)
    else:
        turmas = Turma.objects.all()

    return render(request, 'core/listar_turmas.html', {
        'turmas': turmas,
        'query': query,
    })


@login_required
def cadastrar_turma(request):
    if not request.user.is_superuser:
        return redirect('login')

    erro = None

    if request.method == 'POST':
        nome = request.POST['nome']
        if Turma.objects.filter(nome=nome).exists():
            erro = 'Essa turma já existe.'
        else:
            Turma.objects.create(nome=nome)
            return redirect('listar_turmas')

    return render(request, 'core/cadastrar_turma.html', {'erro': erro})



@login_required
def editar_turma(request, turma_id):
    if not request.user.is_superuser:
        return redirect('login')

    turma = get_object_or_404(Turma, id=turma_id)

    if request.method == 'POST':
        turma.nome = request.POST['nome']
        turma.save()
        return redirect('listar_turmas')

    return render(request, 'core/editar_turma.html', {'turma': turma})


@login_required
def excluir_turma(request, turma_id):
    if not request.user.is_superuser:
        return redirect('login')

    turma = get_object_or_404(Turma, id=turma_id)
    turma.delete()
    return redirect('listar_turmas')



# PROFESSOR
@login_required
def painel_professor(request):
    if not hasattr(request.user, 'professor'):
        return redirect('login')
    professor = request.user.professor
    disciplinas = Disciplina.objects.filter(professor=professor)
    return render(request, 'core/painel_professor.html', {'disciplinas': disciplinas})

    

@login_required
def editar_perfil_professor(request):
    user = request.user

    if request.method == 'POST':
        form = EditarPerfilProfessorForm(request.POST, instance=user)

        if form.is_valid():
            nova_senha = form.cleaned_data.get('nova_senha')

            form.save()  # salva nome, sobrenome, email, etc.

            if nova_senha:  # só altera a senha se foi preenchida
                user.set_password(nova_senha)
                user.save()
                update_session_auth_hash(request, user)  # mantém login ativo
            return redirect('painel_professor')
    else:
        form = EditarPerfilProfessorForm(instance=user)

    return render(request, 'core/editar_perfil_professor.html', {'form': form})

@login_required
def lancar_nota(request, disciplina_id):
    disciplina = get_object_or_404(Disciplina, id=disciplina_id)
    alunos = Aluno.objects.filter(turma=disciplina.turma)

    if request.method == 'POST':
        for aluno in alunos:
            nota_obj, _ = Nota.objects.get_or_create(aluno=aluno, disciplina=disciplina)

            for i in range(1, 5):
                campo = f'nota{i}_{aluno.id}'
                valor_str = request.POST.get(campo)
                if valor_str and valor_str.strip() != '':
                    try:
                        valor = float(valor_str)
                        if 0 <= valor <= 10:
                            setattr(nota_obj, f'nota{i}', valor)
                    except ValueError:
                        pass
                # Se o campo veio vazio ou não existe, não altera o campo para manter a nota antiga

            nota_obj.save()

        # Fica na mesma página após salvar
        return redirect(request.path)

    notas_dict = {}
    for aluno in alunos:
        nota_obj = Nota.objects.filter(aluno=aluno, disciplina=disciplina).first()
        notas_dict[aluno.id] = nota_obj

    return render(request, 'core/lancar_nota.html', {'disciplina': disciplina, 'alunos': alunos, 'notas_dict': notas_dict})



# ALUNO
@login_required
def painel_aluno(request):
    if not hasattr(request.user, 'aluno'):
        return redirect('login')

    aluno = request.user.aluno

    # Todas as disciplinas da turma do aluno
    disciplinas = Disciplina.objects.filter(turma=aluno.turma)

    # Monta um dicionário: disciplina_id -> Nota ou None
    notas_dict = {}
    for disciplina in disciplinas:
        nota = Nota.objects.filter(aluno=aluno, disciplina=disciplina).first()
        notas_dict[disciplina.id] = nota

    return render(request, 'core/painel_aluno.html', {
        'aluno': aluno,
        'disciplinas': disciplinas,
        'notas_dict': notas_dict,
    })


@login_required
def cadastrar_disciplina_para_turma(request, turma_id):
    if not request.user.is_superuser:
        return redirect('login')

    turma = get_object_or_404(Turma, id=turma_id)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        professor_id = request.POST.get('professor')

        if not nome or not professor_id:
            messages.error(request, "Preencha todos os campos.")
        else:
            professor = get_object_or_404(Professor, id=professor_id)

            if Disciplina.objects.filter(nome=nome, turma=turma).exists():
                messages.error(request, "Essa disciplina já existe nesta turma.")
            else:
                Disciplina.objects.create(
                    nome=nome,
                    professor=professor,
                    turma=turma
                )
                messages.success(request, "Disciplina cadastrada com sucesso!")

                # 🔥 REDIRECIONA PARA A LISTA DE DISCIPLINAS DA TURMA
                return redirect('listar_disciplinas_turma', turma_id=turma.id)

    professores = Professor.objects.all()

    return render(request, 'core/cadastrar_disciplina_turma.html', {
        'turma': turma,
        'professores': professores
    })



@login_required
def listar_disciplinas_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)

    query = request.GET.get("q", "")
    disciplinas = Disciplina.objects.filter(turma=turma)

    if query:
        disciplinas = disciplinas.filter(nome__icontains=query)

    return render(request, "core/listar_disciplinas_turma.html", {
        "turma": turma,
        "disciplinas": disciplinas,
        "query": query
    })
