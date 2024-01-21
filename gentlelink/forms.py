from django import forms
from django.contrib.auth.forms import UserChangeForm,  PasswordChangeForm
  
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Tasks, Memos, UserSettings, CoupleUser

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
    

    def clean(self):
        cleaned_data = super().clean()

        title = cleaned_data.get('title')
        description = cleaned_data.get('description')
        deadline = cleaned_data.get('deadline')
        creator_user = cleaned_data.get('creator_user')
        assignment_user = cleaned_data.get('assignment_user')
        status = cleaned_data.get('status')

        if not (title and description and deadline and creator_user and assignment_user and status):
            raise ValidationError("すべてのフィールドに入力してください.")

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

    class Meta:
        model = Tasks
        fields = ['title', 'description', 'deadline', 'creator_user', 'assignment_user', 'complete_at', 'complete_flg']
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

        # CoupleUserを介して夫婦関係を確認
        if CoupleUser.objects.filter(husband=husband_user).exists() or CoupleUser.objects.filter(wife=wife_user).exists():
            raise forms.ValidationError('選択されたユーザーは既に夫婦として登録されています。')

        return cleaned_data
    
class EditMemoForm(forms.ModelForm):
    class Meta:
        model = Memos
        fields = ['content']

class DeleteMemoForm(forms.Form):
    delete = forms.BooleanField(widget=forms.HiddenInput(), initial=False, required=False)    
    