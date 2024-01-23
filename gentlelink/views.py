from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import CreateTaskForm, EditTaskForm, TaskSearchForm, MemoForm, UserSettingsForm, CustomPasswordChangeForm, CoupleRegistrationForm
from .models import Tasks, Memos, Calendars, UserSettings, TaskShares, CoupleUser
from datetime import date
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

def welcome_view(request):
    return render(request, 'welcome.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')  # ユーザー名を取得
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'ユーザー名またはパスワードが正しくありません。')
            
    return render(request, 'login.html')

def signup_view(request):
    if request.method == 'POST':
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:

            user = User.objects.create_user(username=name, email=email, password=password)
            
            login(request, user)
            
            return redirect('login')
    
    return render(request, 'signup.html')


@login_required
def home_view(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    response = redirect('welcome')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def share_task_with_partner(request, task_id):
    task = get_object_or_404(Tasks, id=task_id)
    
    # タスクの作成者か担当者がリクエストしたユーザーであるか確認
    if request.user == task.creator_user or request.user == task.assignment_user:
        # カップルユーザーを取得
        couple_user = CoupleUser.objects.filter(Q(husband=request.user) | Q(wife=request.user)).first()

        if couple_user:
            # カップルユーザーが存在する場合、相手のユーザーを取得
            partner = couple_user.husband if request.user == couple_user.wife else couple_user.wife

            # TaskSharesに自動的に共有するレコードを作成
            TaskShares.objects.get_or_create(task=task, user=partner)
            
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def task_list_view(request, task_id=None):
    shared_tasks = TaskShares.objects.filter(user=request.user).values_list('task', flat=True)
    # 締切日が若いものから順に表示する
    tasks = Tasks.objects.filter(
        Q(creator_user=request.user) | Q(assignment_user=request.user) | Q(id__in=shared_tasks)
    ).order_by('deadline')

    selected_task = None

    if task_id is not None:
        selected_task = get_object_or_404(Tasks, id=task_id)

    return render(request, 'task_list.html', {'tasks': tasks, 'selected_task': selected_task})
    
@login_required
def create_task_view(request):
    if request.method == 'POST':
        
        form = CreateTaskForm(request.POST, user=request.user)
        if form.is_valid():
            
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            deadline = form.cleaned_data['deadline']
            creator_user = form.cleaned_data['creator_user']
            assignment_user = form.cleaned_data['assignment_user']
            complete_at = form.cleaned_data['complete_at']
            status = form.cleaned_data['status']

            status_display = '未完了' if status == 'incomplete' else ('完了' if status == 'complete' else status)

            complete_flg = True if status == 'complete' else False

            new_task = Tasks.objects.create(
                title=title, 
                description=description, 
                deadline=deadline,
                creator_user=creator_user,
                assignment_user=assignment_user,
                complete_at=complete_at,
                complete_flg=complete_flg,  
                status=status_display  
            )

            return redirect('task_list')
    else:
        form = CreateTaskForm(user=request.user)

    return render(request, 'create_task.html', {'form': form})

@login_required
def delete_task_view(request, task_id):
    try:
        task = Tasks.objects.get(id=task_id)
        task.delete()
        return JsonResponse({'success': True})
    except Tasks.DoesNotExist:
        return JsonResponse({'success': False})

@login_required
def task_detail_view(request, task_id):
    task = get_object_or_404(Tasks, id=task_id)
    return render(request, 'task_detail.html', {'task': task})

@login_required
def edit_task_view(request, task_id):
    task = get_object_or_404(Tasks, id=task_id)
    
    if request.method == 'POST':
        form = EditTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_detail', task_id)
    else:
        form = EditTaskForm(instance=task)

    return render(request, 'edit_task.html', {'form': form, 'task': task})

@login_required
def task_search_view(request):
    form = TaskSearchForm(request.GET)
    search_results = []
    from_home = request.GET.get('from_home', None)

    if form.is_valid():
        search_keyword = form.cleaned_data['search_keyword']
        
        if search_keyword:
            # ログインユーザーが紐づけたタスクを取得
            shared_tasks = TaskShares.objects.filter(user=request.user).values_list('task', flat=True)

            # ログインユーザーに紐づくタスクだけを取得
            user_tasks = Tasks.objects.filter(
                Q(creator_user=request.user) | Q(assignment_user=request.user) | Q(id__in=shared_tasks)
            )

            # タイトルまたは説明に検索ワードが含まれるものを取得
            search_results = user_tasks.filter(
                Q(title__icontains=search_keyword) | Q(description__icontains=search_keyword)
            )

    return render(request, 'task_search.html', {'form': form, 'search_results': search_results, 'from_home': from_home})
@login_required
def user_settings(request):
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '変更が保存されました。')
            return redirect('user_settings')  
    else:
        form = UserSettingsForm(instance=request.user)
    
    return render(request, 'user_settings.html', {'form': form})

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'パスワードが変更されました。')
            return redirect('login')  
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'password_change.html', {'form': form})

@login_required
def calendar_view(request):
    # ログインユーザーに紐づくUserSettingsを取得。存在しない場合は作成。
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    # ログインユーザーが紐づけたタスクを取得
    shared_tasks = TaskShares.objects.filter(user=request.user).values_list('task', flat=True)

    # ログインユーザーが作成または紐づけたタスクを取得
    user_tasks = Tasks.objects.filter(
        Q(creator_user=request.user) | Q(assignment_user=request.user) | Q(id__in=shared_tasks)
    )

    event_data = []
    for task in user_tasks:
        if task.deadline:
            event_data.append({
                'title': task.title,
                'start': task.deadline.isoformat(),
                'url': f'/gentlelink/memo_detail/create/?date={task.deadline.date()}',
            })
    
    # カラーテーマの取得
    user_settings = UserSettings.objects.get(user=request.user)
    calendar_color = user_settings.calendar_color

    return render(request, 'calendar.html', {'event_data': event_data, 'calendar_color': calendar_color })

class MemoDetailView(View):
    template_name = 'memo_detail.html'

    def get(self, request, *args, **kwargs):
        date = self.request.GET.get('date')
        memos = Memos.objects.filter(date=date, user=request.user)
        form = MemoForm()
        return render(request, self.template_name, {'memos': memos, 'date': date, 'form': form})
    
    def post(self, request, *args, **kwargs):
        date = self.request.GET.get('date')
        form = MemoForm(request.POST)
        
        if form.is_valid():
            content = form.cleaned_data['content']
            user = request.user

            calendar_instance = Calendars.objects.first()

            memo = Memos(content=content, date=date, user=user, calendar=calendar_instance)
            memo.save()
        
        return redirect(reverse('memo_create') + f'?date={date}')

class EditMemoView(View):
    template_name = 'edit_memo.html'

    def get(self, request, *args, **kwargs):
        memo_id = kwargs.get('id')

        if memo_id:
            memo = Memos.objects.get(id=memo_id)
            form = MemoForm(instance=memo)
        else:
            form = MemoForm()

        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = MemoForm(request.POST)

        if form.is_valid():
            content = form.cleaned_data['content']
            user = request.user
            date = form.cleaned_data.get('date', None)

            memo_id = kwargs.get('id')

            if memo_id:
                memo = Memos.objects.get(id=memo_id)
                memo.content = content
                memo.save()
            else:
                calendar_instance = Calendars.objects.first()
                memo = Memos(content=content, date=date, user=user, calendar=calendar_instance)
                memo.save()

            messages.success(request, '変更が保存されました.')
            return redirect('memo_edit', id=memo_id)

        return render(request, self.template_name, {'form': form})

    def delete(self, request, *args, **kwargs):
        memo_id = kwargs.get('id')

        if memo_id:
            try:
                memo = Memos.objects.get(id=memo_id)
                memo.delete()
                return JsonResponse({'success': True})
            except Memos.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'メモが見つかりませんでした。'})

        return JsonResponse({'success': False, 'error': 'メモIDが指定されていません。'})

@login_required
def notification_view(request):
    # ログインユーザーが紐づけたタスクを取得
    shared_tasks = TaskShares.objects.filter(user=request.user).values_list('task', flat=True)

    # ログインユーザーが作成または紐づけた未完了タスクを取得
    incomplete_tasks = Tasks.objects.filter(
        (Q(creator_user=request.user) | Q(assignment_user=request.user) | Q(id__in=shared_tasks)) &
        Q(complete_flg=False)
    ).order_by('deadline', 'created_at')  # 締切日が若いものから順に、同じ場合は作成日が若いものから順に

    if request.method == 'POST':
        
        completed_task_ids = request.POST.getlist('task_id')
        # 選択されたタスクを完了済みに設定
        Tasks.objects.filter(id__in=completed_task_ids).update(complete_flg=True, complete_at=timezone.now())
        return redirect('notification')

    return render(request, 'notification.html', {'tasks': incomplete_tasks})

@login_required
def couple_registration_view(request):
    if request.method == 'POST':
        form = CoupleRegistrationForm(request.POST)
        if form.is_valid():
            husband_username = form.cleaned_data['husband_username']
            wife_username = form.cleaned_data['wife_username']

            husband_user = User.objects.get(username=husband_username)
            wife_user = User.objects.get(username=wife_username)

            # CoupleUser モデルに夫婦情報を保存
            couple_user = CoupleUser.objects.create(husband=husband_user, wife=wife_user)
            
            return redirect('couple_registration_success')  
    else:
        form = CoupleRegistrationForm()

    return render(request, 'couple_registration.html', {'form': form})

@login_required
def couple_registration_success_view(request):
    return render(request, 'couple_registration_success.html')

@login_required
def settings_view(request):
    if request.method == 'POST':
        calendar_color = request.POST.get('calendar_color')
        user_settings, created = UserSettings.objects.get_or_create(user=request.user)
        user_settings.calendar_color = calendar_color
        user_settings.save()
        return redirect('calendar') 
    else:
        # POST リクエスト以外の場合は通常の settings.html を表示
        return render(request, 'settings.html')

