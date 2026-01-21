from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Professor, Aluno, Disciplina, Turma, Nota, Gestor
from .forms import (
    LoginForm, ProfessorForm, AlunoForm, DisciplinaForm, TurmaForm,
    NotaForm, EditarPerfilForm, GestorForm
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
            return redirect('painel_super')

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
                return redirect('painel_super')  # <- adicionado
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('login')



from datetime import datetime
import calendar

def gerar_calendario():
    hoje = datetime.today()
    ano = hoje.year
    mes = hoje.month

    cal = calendar.monthcalendar(ano, mes)
    celulas = []

    for semana in cal:
        for dia in semana:
            celulas.append({
                "numero": dia,
                "vazio": dia == 0,
                "hoje": dia == hoje.day,
            })

    return celulas

# -------------------- SUPERUSUÁRIO --------------------
def is_superuser(user):
    return user.is_superuser

def is_super_ou_gestor(user):
    return user.is_superuser or hasattr(user, 'gestor')



@login_required
@user_passes_test(is_super_ou_gestor)
def painel_super(request):
    foto_perfil_url = get_foto_perfil(request.user)
    ano_atual = datetime.now().year

    # 🔥 FILTRO DE ANO
    # Busca todos os anos disponíveis das turmas
    anos_disponiveis_qs = Turma.objects.values_list('ano', flat=True).distinct().order_by('-ano')
    anos_disponiveis = list(anos_disponiveis_qs)
    
    # Se não houver turmas, adiciona o ano atual
    if not anos_disponiveis:
        anos_disponiveis = [ano_atual]
    
    # Pega o ano do filtro (GET) ou usa o ano atual
    ano_filtro = request.GET.get('ano')
    try:
        ano_filtro = int(ano_filtro) if ano_filtro else ano_atual
    except ValueError:
        ano_filtro = ano_atual
    
    # Garante que o ano_filtro existe na lista
    if ano_filtro not in anos_disponiveis:
        anos_disponiveis.append(ano_filtro)
        anos_disponiveis.sort(reverse=True)

    # Contagem para turmas do ano filtrado (em vez de ano_atual)
    turmas_ano_filtrado = Turma.objects.filter(ano=ano_filtro)

    total_turmas = turmas_ano_filtrado.count()
    total_alunos = Aluno.objects.filter(turma__in=turmas_ano_filtrado).distinct().count()
    total_professores = Professor.objects.filter(disciplina__turma__in=turmas_ano_filtrado).distinct().count()
    total_disciplinas = Disciplina.objects.filter(turma__in=turmas_ano_filtrado).distinct().count()

    return render(request, "core/painel_super.html", {
        "usuario": request.user,
        "nome_exibicao": get_nome_exibicao(request.user),
        "total_professores": total_professores,
        "total_alunos": total_alunos,
        "total_turmas": total_turmas,
        "total_disciplinas": total_disciplinas,
        "foto_perfil_url": foto_perfil_url,
        "agora": datetime.now(),
        "calendario": gerar_calendario(),
        "anos_disponiveis": anos_disponiveis,  # ✅ Novo
        "ano_filtro": ano_filtro,              # ✅ Novo
    })

@login_required
def usuarios(request):
    pode_ver_gestores = False

    if request.user.is_superuser:
        pode_ver_gestores = True
    elif hasattr(request.user, 'gestor'):
        if request.user.gestor.cargo in ('diretor', 'vice_diretor'):
            pode_ver_gestores = True

    return render(request, "core/usuarios.html", {
        "pode_ver_gestores": pode_ver_gestores
    })


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect

@login_required
def editar_perfil(request):
    user = request.user

    # Detecta perfil associado
    perfil = None
    if hasattr(user, "professor"):
        perfil = user.professor
    elif hasattr(user, "aluno"):
        perfil = user.aluno
    elif hasattr(user, "gestor"):
        perfil = user.gestor
    # superusuário pode não ter perfil e está ok

    if request.method == "POST":
        form = EditarPerfilForm(request.POST, instance=user)

        if form.is_valid():
            # ---------------------------
            # 📧 Salva dados básicos
            # ---------------------------
            user = form.save(commit=False)

            # ---------------------------
            # 🔐 Troca de senha (se houver)
            # ---------------------------
            nova_senha = form.cleaned_data.get("nova_senha")
            if nova_senha:
                user.set_password(nova_senha)
                user.save()
                update_session_auth_hash(request, user)
            else:
                user.save()

            # ---------------------------
            # 📸 Foto de perfil
            # ---------------------------
            foto = request.FILES.get("foto")
            if perfil and foto:
                perfil.foto = foto
                perfil.save()

            messages.success(request, "Perfil atualizado com sucesso!")

            # ---------------------------
            # 🔁 Redirecionamento
            # ---------------------------
            if user.is_superuser:
                return redirect("painel_super")
            if hasattr(user, "professor"):
                return redirect("painel_professor")
            if hasattr(user, "aluno"):
                return redirect("painel_aluno")
            if hasattr(user, "gestor"):
                return redirect("painel_super")

            return redirect("login")

        else:
            # Erros do form (senha, email, etc.)
            messages.error(request, "Corrija os erros abaixo.")

    else:
        form = EditarPerfilForm(instance=user)

    # Foto atual
    foto_atual = perfil.foto.url if perfil and perfil.foto else None

    return render(request, "core/editar_perfil.html", {
        "form": form,
        "perfil": perfil,
        "foto_atual": foto_atual,
        "foto_perfil_url": get_foto_perfil(user),
    })




def get_foto_perfil(user):
    # Professor
    try:
        if hasattr(user, "professor") and user.professor.foto:
            return user.professor.foto.url
    except:
        pass

    # Aluno
    try:
        if hasattr(user, "aluno") and user.aluno.foto:
            return user.aluno.foto.url
    except:
        pass

    # Gestor
    try:
        if hasattr(user, "gestor") and user.gestor.foto:
            return user.gestor.foto.url
    except:
        pass

    # SUPERSUÁRIO
    try:
        if hasattr(user, "superperfil") and user.superperfil.foto:
            return user.superperfil.foto.url
    except:
        pass

    return None


@login_required
def remover_foto_perfil(request):
    user = request.user

    # detecta perfil (professor, aluno ou gestor)
    perfil = None
    if hasattr(user, "professor"):
        perfil = user.professor
    elif hasattr(user, "aluno"):
        perfil = user.aluno
    elif hasattr(user, "gestor"):
        perfil = user.gestor

    if not perfil:
        messages.error(request, "Nenhum perfil associado ao usuário.")
        return redirect("editar_perfil")

    # remove a foto se existir
    if perfil.foto:
        perfil.foto.delete(save=False)  # apaga o arquivo físico
        perfil.foto = None
        perfil.save()

    messages.success(request, "Foto removida com sucesso!")
    return redirect("editar_perfil")

def get_nome_exibicao(user):
    if hasattr(user, 'gestor'):
        return user.gestor.nome_completo

    if hasattr(user, 'professor'):
        return user.professor.nome_completo

    if hasattr(user, 'aluno'):
        return user.aluno.nome_completo

    # Superusuário
    nome = f"{user.first_name} {user.last_name}".strip()
    if nome:
        return nome

    # Último fallback (nunca deveria acontecer)
    return user.email



# -------------------- PROFESSORES --------------------
@login_required
@user_passes_test(is_superuser)
def listar_professores(request):
    query = request.GET.get('q', '')
    professores = Professor.objects.filter(nome_completo__icontains=query) if query else Professor.objects.all()
    return render(request, 'core/listar_professores.html', {'professores': professores, 'query': query})


from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Professor


@login_required
@user_passes_test(is_superuser)
def cadastrar_professor(request):
    if request.method == 'POST':
        form = ProfessorForm(request.POST, request.FILES, request=request)

        if form.is_valid():
            professor = form.save()
            
            messages.success(
                request,
                f"Professor(a) {professor.nome_completo} cadastrado(a) com sucesso!"
            )
            return redirect('listar_professores')
        else:
            for campo, erros in form.errors.items():
                for erro in erros:
                    messages.error(request, erro)
    else:
        form = ProfessorForm(request=request)

    return render(request, 'core/cadastrar_professor.html', {'form': form})



@login_required
@user_passes_test(is_superuser)
def editar_professor(request, professor_id):
    professor = get_object_or_404(Professor, id=professor_id)
    
    if request.method == 'POST':
        form = ProfessorForm(request.POST, request.FILES, instance=professor, request=request)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Professor(a) {professor.nome_completo} atualizado(a) com sucesso!')
            return redirect('listar_professores')
        else:
            for campo, erros in form.errors.items():
                for erro in erros:
                    messages.error(request, erro)
    else:
        form = ProfessorForm(instance=professor, request=request)

    return render(request, 'core/cadastrar_professor.html', {'form': form, 'professor': professor})


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
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'gestor') and u.gestor.cargo in ['diretor', 'vice_diretor']))
def cadastrar_gestor(request):
    if request.method == 'POST':
        form = GestorForm(request.POST, request.FILES, request=request)

        if form.is_valid():
            gestor = form.save()  # 🔥 Faz tudo automaticamente
            
            messages.success(
                request,
                f"{gestor.get_cargo_display()} {gestor.nome_completo} cadastrado com sucesso!"
            )
            return redirect('listar_gestores')
        else:
            for campo, erros in form.errors.items():
                for erro in erros:
                    messages.error(request, erro)
    else:
        form = GestorForm(request=request)

    return render(request, 'core/cadastrar_gestor.html', {'form': form})


# ---- GESTOR (Painel da Gestão Escolar) ----



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
def editar_gestor(request, gestor_id):
    gestor = get_object_or_404(Gestor, id=gestor_id)
    user = gestor.user

    # Permissão: superusuário ou o próprio gestor
    is_super = request.user.is_superuser
    is_mesmo_gestor = hasattr(request.user, 'gestor') and request.user.gestor == gestor

    if not (is_super or is_mesmo_gestor):
        messages.error(request, "Você não tem permissão para editar este gestor.")
        return redirect('painel_super')

    if request.method == 'POST':
        form = GestorForm(request.POST,request.FILES, instance=gestor, request=request)
        if form.is_valid():
            form.save()

            # Atualiza senha se foi informada
            nova_senha = form.cleaned_data.get("senha")
            if nova_senha:
                user.set_password(nova_senha)
                user.save()

                # Mantém sessão ativa caso seja o próprio gestor alterando a senha
                if is_mesmo_gestor:
                    update_session_auth_hash(request, user)

            messages.success(request, "Gestor atualizado com sucesso!")

            # 🔥 Redirecionamento correto:
            # Superusuário volta para a lista de gestores
            if is_super:
                return redirect('listar_gestores')

            # Gestor comum volta ao painel dele
            return redirect('painel_super')

        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = GestorForm(instance=gestor, initial={'email': user.email})

    return render(request, 'core/cadastrar_gestor.html', {'form': form, 'gestor': gestor})




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
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES, request=request)

        if form.is_valid():
            aluno = form.save()  # 🔥 O form já cria User e Aluno!
            
            messages.success(
                request,
                f"Aluno(a) {aluno.nome_completo} cadastrado(a) com sucesso!"
            )
            return redirect('listar_alunos')
        else:
            for campo, erros in form.errors.items():
                for erro in erros:
                    messages.error(request, erro)
    else:
        form = AlunoForm(request=request)

    return render(request, 'core/cadastrar_aluno.html', {'form': form})

@login_required
@user_passes_test(is_superuser)
def editar_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)

    if request.method == 'POST':
        form = AlunoForm(
            request.POST,
            request.FILES,
            instance=aluno,
            request=request
        )

        if form.is_valid():
            aluno = form.save()
            messages.success(
                request,
                f"Aluno(a) {aluno.nome_completo} atualizado(a) com sucesso!"
            )
            return redirect('listar_alunos')
        else:
            for campo, erros in form.errors.items():
                for erro in erros:
                    messages.error(request, erro)
    else:
        form = AlunoForm(instance=aluno, request=request)

    return render(request, 'core/cadastrar_aluno.html', {
        'form': form,
        'aluno': aluno
    })


@login_required
@user_passes_test(is_superuser)
def excluir_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    aluno.user.delete()
    aluno.delete()
    messages.success(request, 'Aluno removido.')
    return redirect('listar_alunos')







# -------------------- DISCIPLINAS, TURMAS E NOTAS --------------------
# (mantém as lógicas originais do seu código, já estavam certas)


#Disciplinas


@login_required
def visualizar_disciplinas(request, disciplina_id):
    if not request.user.is_superuser:
        return redirect('login')
    
    disciplina = get_object_or_404(Disciplina, id=disciplina_id)
    turma = disciplina.turma
    alunos = Aluno.objects.filter(turma=turma)
    notas = Nota.objects.filter(disciplina=disciplina)
    notas_dict = { 
        nota.aluno.id: nota
        for nota in Nota.objects.filter(disciplina=disciplina) 
        }

    context={
        "disciplina":disciplina,
        "turma":turma,
        "alunos":alunos,
        "notas":notas,
        "notas_dict": notas_dict
    }

    return render(request,'core/visualizar_disciplinas.html', context)



@login_required
def editar_disciplina(request, disciplina_id):
    if not request.user.is_superuser:
        return redirect('login')

    disciplina = get_object_or_404(Disciplina, id=disciplina_id)

    if request.method == 'POST':
        disciplina.nome = request.POST['nome']
        disciplina.professor = get_object_or_404(
            Professor,
            id=request.POST['professor']
        )
        disciplina.save()

        return redirect(
            'listar_disciplinas_turma',
            turma_id=disciplina.turma.id
        )

    professores = Professor.objects.filter(user__is_superuser=False)

    return render(request, 'core/cadastrar_disciplina_turma.html', {
        'disciplina': disciplina,
        'turma': disciplina.turma,
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
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Turma

@login_required
def listar_turmas(request):
    if not request.user.is_superuser:
        return redirect('login')

    ano_atual = timezone.localtime(timezone.now()).year
    query = request.GET.get('q', '').strip()

    # TODOS os anos disponíveis no banco, descendente
    anos_disponiveis_qs = Turma.objects.values_list('ano', flat=True).distinct().order_by('-ano')
    anos_disponiveis = list(anos_disponiveis_qs)

    # Se não houver turmas no banco, adiciona o ano atual
    if not anos_disponiveis:
        anos_disponiveis = [ano_atual]

    # Filtro do ano
    ano_filtro = request.GET.get('ano')
    try:
        ano_filtro = int(ano_filtro) if ano_filtro else ano_atual
    except ValueError:
        ano_filtro = ano_atual

    # Garantir que o ano_filtro existe no banco ou pelo menos no ano atual
    if ano_filtro not in anos_disponiveis:
        anos_disponiveis.append(ano_filtro)
        anos_disponiveis.sort(reverse=True)

    # Filtra as turmas
    turmas = Turma.objects.filter(ano=ano_filtro)
    if query:
        turmas = turmas.filter(nome__icontains=query)

    return render(request, 'core/listar_turmas.html', {
        'turmas': turmas,
        'query': query,
        'ano_filtro': ano_filtro,
        'anos_disponiveis': anos_disponiveis
    })




from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Turma

@login_required
def cadastrar_turma(request):
    if not request.user.is_superuser:
        return redirect('login')

    erro = None

    ano_atual = datetime.now().year
    anos = list(range(2010, ano_atual + 2))  # 2010 até ano atual + 1

    if request.method == 'POST':
        nome = request.POST.get('nome')
        turno = request.POST.get('turno')
        ano = request.POST.get('ano')

        # -------- VALIDAÇÕES --------
        try:
            ano = int(ano)
        except (TypeError, ValueError):
            erro = 'Ano letivo inválido.'
        else:
            if ano < 2010 or ano > ano_atual + 1:
                erro = 'O ano letivo deve ser entre 2010 e o próximo ano.'
            elif Turma.objects.filter(nome=nome, ano=ano).exists():
                erro = 'Essa turma já existe neste ano.'
            else:
                Turma.objects.create(
                    nome=nome,
                    turno=turno,
                    ano=ano
                )
                return redirect('listar_turmas')

    return render(
        request,
        'core/cadastrar_turma.html',
        {
            'erro': erro,
            'anos': anos
        }
    )




@login_required
def editar_turma(request, turma_id):
    if not request.user.is_superuser:
        return redirect('login')

    turma = Turma.objects.get(id=turma_id)
    erro = None

    if request.method == "POST":
        nome = request.POST.get('nome')
        turno = request.POST.get('turno')
        ano = request.POST.get('ano')

        if Turma.objects.filter(nome=nome, ano=ano).exclude(id=turma.id).exists():
            erro = 'Já existe outra turma com esse nome neste ano.'
        else:
            turma.nome = nome
            turma.turno = turno
            turma.ano = ano
            turma.save()
            messages.success(request, "Turma atualizada com sucesso!")
            return redirect('listar_turmas')

    return render(request, 'core/cadastrar_turma.html', {
        'turma': turma,
        'erro': erro
    })



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
    foto_perfil_url = get_foto_perfil(request.user)
    return render(request, 'core/painel_professor.html', {
        'disciplinas': disciplinas,
        'foto_perfil_url': foto_perfil_url,
    })

    




from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

@login_required
def lancar_nota(request, disciplina_id):
    disciplina = get_object_or_404(Disciplina, id=disciplina_id)

    # FORÇA queryset de MODEL (sem values)
    alunos = Aluno.objects.filter(turma_id=disciplina.turma_id).order_by('nome_completo')

    # DEBUG no terminal (pra provar que tem id)
    if alunos.exists():
        a0 = alunos.first()
        print("DEBUG ALUNO:", type(a0), "id=", a0.id, "pk=", a0.pk, "nome=", a0.nome_completo)

    if request.method == 'POST':
        for aluno in alunos:
            nota_obj, _ = Nota.objects.get_or_create(
                aluno_id=aluno.pk,
                disciplina_id=disciplina.id
            )

            for i in range(1, 5):
                campo = f'nota{i}_{aluno.pk}'
                valor = request.POST.get(campo, '').strip()

                if valor == '':
                    continue

                try:
                    valor_float = float(valor.replace(',', '.'))
                except ValueError:
                    messages.error(request, f'Nota inválida: "{valor}" para {aluno.nome_completo} (B{i}).')
                    continue

                setattr(nota_obj, f'nota{i}', valor_float)

            nota_obj.save()

        messages.success(request, 'Notas salvas com sucesso!')
        return redirect('lancar_nota', disciplina_id=disciplina.id)

    notas_dict = {n.aluno_id: n for n in Nota.objects.filter(disciplina_id=disciplina.id)}

    return render(request, 'core/lancar_nota.html', {
        'disciplina': disciplina,
        'alunos': alunos,
        'notas_dict': notas_dict,
    })




# ALUNO
# VIEW DO PAINEL DO ALUNO - ATUALIZADA
@login_required
def painel_aluno(request):
    if not hasattr(request.user, 'aluno'):
        return redirect('login')

    aluno = request.user.aluno

    # Disciplinas e notas
    disciplinas = Disciplina.objects.filter(turma=aluno.turma)
    
    disciplinas_com_notas = []
    soma_medias = 0
    total_disciplinas_com_media = 0
    total_notas_lancadas = 0
    total_notas_possiveis = disciplinas.count() * 4  # 4 bimestres
    
    for disciplina in disciplinas:
        nota = Nota.objects.filter(aluno=aluno, disciplina=disciplina).first()
        
        if nota:
            # Contar quantas notas foram lançadas
            if nota.nota1 is not None:
                total_notas_lancadas += 1
            if nota.nota2 is not None:
                total_notas_lancadas += 1
            if nota.nota3 is not None:
                total_notas_lancadas += 1
            if nota.nota4 is not None:
                total_notas_lancadas += 1
        
        disciplinas_com_notas.append({
            "disciplina": disciplina,
            "nota": nota
        })
        
        # Calcular média geral
        if nota and nota.media:
            soma_medias += nota.media
            total_disciplinas_com_media += 1
    
    # Média geral do aluno
    media_geral = soma_medias / total_disciplinas_com_media if total_disciplinas_com_media > 0 else None

    # Grade horária
    try:
        grade_obj = GradeHorario.objects.get(turma=aluno.turma)
        grade_horario = grade_obj.dados
    except GradeHorario.DoesNotExist:
        grade_horario = None

    # Calendário
    calendario = gerar_calendario()
    agora = datetime.now()

    return render(request, 'core/painel_aluno.html', {
        "aluno": aluno,
        "disciplinas_com_notas": disciplinas_com_notas,
        "media_geral": media_geral,
        "total_notas_lancadas": total_notas_lancadas,
        "total_notas_possiveis": total_notas_possiveis,
        "grade_horario": grade_horario,
        "calendario": calendario,
        "agora": agora,
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
                return redirect('listar_disciplinas_turma', turma_id=turma.id)

    professores = Professor.objects.filter(user__is_superuser=False)

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


# helper para pegar foto do usuário de forma segura
def get_foto_perfil(user):
    # Professor
    try:
        if hasattr(user, "professor") and user.professor.foto:
            return user.professor.foto.url
    except:
        pass

    # Aluno
    try:
        if hasattr(user, "aluno") and user.aluno.foto:
            return user.aluno.foto.url
    except:
        pass

    # Gestor
    try:
        if hasattr(user, "gestor") and user.gestor.foto:
            return user.gestor.foto.url
    except:
        pass

    return None



from .models import GradeHorario

from .models import GradeHorario
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required




from .models import GradeHorario
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

HORARIOS = {
    "manha": [
        "07:00 às 07:45",
        "07:45 às 08:30",
        "08:50 às 09:35",
        "09:35 às 10:20",
        "10:30 às 11:15",
        "11:15 às 12:00",
    ],
    "tarde": [
        "13:00 às 13:45",
        "13:45 às 14:30",
        "14:50 às 15:35",
        "15:35 às 16:20",
        "16:30 às 17:15",
        "17:15 às 18:00",
    ],
    "noite": [
        "19:00 às 19:45",
        "19:45 às 20:30",
        "20:40 às 21:25",
        "21:25 às 22:00",
    ],
}

@login_required
def grade_horaria(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    grade, criado = GradeHorario.objects.get_or_create(turma=turma)

    dias = ["segunda", "terca", "quarta", "quinta", "sexta"]
    nomes_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]

    turno_key = (
        turma.turno.lower()
        .replace("ã", "a")
        .replace("á", "a")
    )

    horarios = HORARIOS.get(turno_key, [])

    if not horarios:
        messages.error(request, "Turno inválido nesta turma.")
        horarios = [""]

    if not grade.dados:
        grade.dados = {dia: [""] * len(horarios) for dia in dias}
        grade.save()

    disciplinas_turma = Disciplina.objects.filter(turma=turma)

    # ----------------------------------------------
    # 1) MAPEAR TODAS AS OCUPAÇÕES DE PROFESSORES
    # ----------------------------------------------
    ocupados = {}   # {professor_id: {(dia, index)} }

    outras_grades = GradeHorario.objects.exclude(turma=turma)

    for g in outras_grades:
        for dia in dias:
            lista = g.dados.get(dia, [])
            for idx, nome_disciplina in enumerate(lista):
                if not nome_disciplina:
                    continue

                try:
                    disc = Disciplina.objects.get(nome=nome_disciplina, turma=g.turma)
                except Disciplina.DoesNotExist:
                    continue

                prof = disc.professor_id

                if prof not in ocupados:
                    ocupados[prof] = set()

                ocupados[prof].add((dia, idx))

    # ----------------------------------------------
    # 2) SALVAR (POST)
    # ----------------------------------------------
    if request.method == "POST":
        new_data = {dia: [] for dia in dias}

        for i in range(len(horarios)):
            for dia in dias:
                campo = f"{dia}_{i}"
                valor = request.POST.get(campo, "")
                new_data[dia].append(valor)

        grade.dados = new_data
        grade.save()

        messages.success(request, "Grade horária atualizada com sucesso!")
        return redirect("grade_horaria", turma_id=turma.id)

    # ----------------------------------------------
    # 3) MONTAR TABELA PARA O TEMPLATE
    #     → Aqui vamos filtrar disciplinas ocupadas
    # ----------------------------------------------
    rows = []
    for i, horario in enumerate(horarios):
        row = {"index": i, "horario": horario, "cols": []}

        for dia in dias:

            # valor atual da célula
            lista = grade.dados.get(dia, [])
            valor = ""
            if isinstance(lista, list) and i < len(lista):
                valor = lista[i] or ""

            # ----------------------------
            # FILTRAR DISCIPLINAS DISPONÍVEIS
            # ----------------------------
            disciplinas_disponiveis = []
            for d in disciplinas_turma:

                prof_id = d.professor_id

                # se o professor está ocupado neste dia e horário → pula
                if prof_id in ocupados and (dia, i) in ocupados[prof_id]:
                    continue

                disciplinas_disponiveis.append(d)

            row["cols"].append({
                "dia": dia,
                "valor": valor,
                "disciplinas": disciplinas_disponiveis,  # ← envia disciplinas filtradas para este horário/dia
            })

        rows.append(row)

    return render(request, "core/grade_horaria.html", {
        "turma": turma,
        "nomes_dias": nomes_dias,
        "rows": rows,
        "disciplinas": disciplinas_turma,  # ainda enviado para o loop externo
    })
