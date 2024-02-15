from django import forms
from django.contrib.auth.forms import UserChangeForm,  PasswordChangeForm
  
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Tasks, Memos, UserSettings, CoupleUser
from django.utils import timezone
from django.db.models import Q


class CreateTaskForm(forms.Form):
    title = forms.CharField(label='タイトル', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label='説明', widget=forms.Textarea(attrs={'class': 'form-control'}))
    deadline = forms.DateTimeField(label='締切', widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    creator_user = forms.ModelChoiceField(label='作成者', queryset=User.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    assignment_user = forms.ModelChoiceField(label='担当者', queryset=User.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}))
    complete_at = forms.DateTimeField(label='完了予定日時', widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    
    STATUS_CHOICES = [
        ('incomplete', '未完了'),
        ('complete', '完了'),
    ]

    status = forms.ChoiceField(label='進捗状況', choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')

        if deadline and deadline < timezone.now():
            raise ValidationError("締切日時を過去に指定することは出来ません。")

        return deadline

    def clean_complete_at(self):
        complete_at = self.cleaned_data.get('complete_at')

        if complete_at and complete_at < timezone.now():
            raise ValidationError("完了予定日時を過去に指定することは出来ません。")

        return complete_at
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # ユーザー情報を取得
        super(CreateTaskForm, self).__init__(*args, **kwargs)

        # ユーザーが指定されている場合は、そのユーザーとその紐づけたユーザーを選択肢とする
        if user:
            # ログインユーザーとその紐づけたユーザーのIDリストを取得
            user_ids = [user.id]
            user_ids += CoupleUser.objects.filter(husband=user).values_list('wife_id', flat=True)
            user_ids += CoupleUser.objects.filter(wife=user).values_list('husband_id', flat=True)

            # 上記のIDリストに対応するUserオブジェクトを取得し、担当者の選択肢とする
            self.fields['assignment_user'].queryset = User.objects.filter(id__in=user_ids)
            self.fields['creator_user'].queryset = User.objects.filter(pk=user.pk)

class EditTaskForm(forms.ModelForm):
    deadline = forms.DateTimeField(label='締切', widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    complete_at = forms.DateTimeField(label='完了予定日時', widget=forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    STATUS_CHOICES = [
        ('incomplete', '未完了'),
        ('complete', '完了'),
    ]

    status = forms.ChoiceField(label='進捗状況', choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        linked_user = kwargs.pop('linked_user', None)
        login_user = kwargs.pop('login_user', None)
        
        super(EditTaskForm, self).__init__(*args, **kwargs)

        # ログインユーザーとその関連ユーザーのみを選択肢とする
        assignment_user_queryset = User.objects.none()

        if login_user:
            user_ids = [login_user.id]
            user_ids += CoupleUser.objects.filter(husband=login_user).values_list('wife_id', flat=True)
            user_ids += CoupleUser.objects.filter(wife=login_user).values_list('husband_id', flat=True)
            assignment_user_queryset = User.objects.filter(id__in=user_ids)

        self.fields['assignment_user'].queryset = assignment_user_queryset

        # タスクの情報を初期値として設定
        if 'instance' in kwargs:
            task = kwargs['instance']
            self.fields['status'].initial = task.status

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now():
            raise forms.ValidationError("締切日時を過去に指定することは出来ません。")
        return deadline

    def clean_complete_at(self):
        complete_at = self.cleaned_data.get('complete_at')
        if complete_at and complete_at < timezone.now():
            raise forms.ValidationError("完了予定日時を過去に指定することは出来ません。")
        return complete_at

    class Meta:
        model = Tasks
        fields = ['title', 'description', 'deadline', 'creator_user', 'assignment_user', 'complete_at', 'status']
        widgets = {
            'deadline': forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'complete_at': forms.TextInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
        
class TaskSearchForm(forms.Form):
    search_keyword = forms.CharField(label='検索ワード', required=False)       

class MemoForm(forms.ModelForm):
    class Meta:
        model = Memos
        fields = ['content']
        
class UserSettingsForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email']
              
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = '現在のパスワード'
        self.fields['new_password1'].label = '新しいパスワード'
        self.fields['new_password2'].label = '新しいパスワード (確認用)'

        # バリデーションメッセージを空にする
        self.error_messages = {
            'password_mismatch': '',
            'password_incorrect': '',
            'password_too_short': '',
            'password_common': '',
        }
        
class CoupleRegistrationForm(forms.Form):
    husband_username = forms.CharField(label='パパのユーザー名')
    wife_username = forms.CharField(label='ママのユーザー名')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # ログインユーザーを取得
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        husband_username = cleaned_data.get('husband_username')
        wife_username = cleaned_data.get('wife_username')

        # ユーザーが存在するか確認
        try:
            husband_user = User.objects.get(username=husband_username)
            wife_user = User.objects.get(username=wife_username)
        except User.DoesNotExist:
            raise forms.ValidationError('指定されたユーザーが存在しません。')

        # ログインユーザーがパパまたはママのユーザー名に含まれているか確認
        if self.user.username not in [husband_username, wife_username]:
            raise forms.ValidationError('どちらかに自分のユーザー名を入力してください。')

        # 同一アカウントでないことを確認
        if husband_username == wife_username:
            raise forms.ValidationError('同一のアカウントは紐づけすることが出来ません。')
        
        # CoupleUserを介して夫婦関係を確認
        if CoupleUser.objects.filter(husband=husband_user).exists() or CoupleUser.objects.filter(wife=wife_user).exists():
            raise forms.ValidationError('相手ユーザーは既に他ユーザーと紐づけされています。')

        # すでに他のユーザーと紐づけされているか確認
        if CoupleUser.objects.exclude(Q(husband=husband_user) | Q(wife=wife_user)).filter(
            Q(husband=husband_user) | Q(wife=wife_user)
        ).exists():
            raise forms.ValidationError('相手のアカウントは既に他のアカウントと紐づけされています。')

         # 相手ユーザーがパパまたはママとして他ユーザーと紐づけされている場合はエラー
        if CoupleUser.objects.filter(husband=wife_user).exists() or CoupleUser.objects.filter(wife=husband_user).exists():
            raise forms.ValidationError('相手ユーザーは既に他ユーザーと紐づけされています。')
        
        return cleaned_data
    
class EditMemoForm(forms.ModelForm):
    class Meta:
        model = Memos
        fields = ['content']

class DeleteMemoForm(forms.Form):
    delete = forms.BooleanField(widget=forms.HiddenInput(), initial=False, required=False)    
    