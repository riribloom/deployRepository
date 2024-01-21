from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    calendar_color = models.CharField(max_length=50, null=True, blank=True) 

    COLOR_THEME_CHOICES = [
        ('default', 'デフォルト'),
        ('dark', 'ダークモード'),
    ]
  
    font_style = models.CharField(max_length=50, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @staticmethod
    def create_user_settings(sender, instance, created, **kwargs):
        if created:
            UserSettings.objects.create(user=instance, calendar_color='default')

# ユーザーが保存されるたびに create_user_settings が呼ばれるように
models.signals.post_save.connect(UserSettings.create_user_settings, sender=User)
    
class Tasks(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateTimeField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('incomplete', '未完了'),
        ('complete', '完了'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    creator_user = models.ForeignKey(User, related_name='creator_tasks', on_delete=models.CASCADE)
    assignment_user = models.ForeignKey(User, related_name='assigned_tasks', on_delete=models.CASCADE)
    complete_flg = models.BooleanField(default=False)
    complete_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

class Memos(models.Model):
    content = models.TextField()
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    calendar = models.ForeignKey('Calendars', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Calendars(models.Model):
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Notifications(models.Model):
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Assignments(models.Model):
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TaskShares(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CoupleUser(models.Model):
    husband = models.OneToOneField(User, related_name='couple_user_husband', on_delete=models.CASCADE)
    wife = models.OneToOneField(User, related_name='couple_user_wife', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.husband.username} & {self.wife.username}'

@receiver(post_save, sender=CoupleUser)
def couple_user_created(sender, instance, created, **kwargs):
    if created:
        husband_tasks = Tasks.objects.filter(creator_user=instance.husband)
        wife_tasks = Tasks.objects.filter(creator_user=instance.wife)

        for task in husband_tasks:
            TaskShares.objects.get_or_create(task=task, user=instance.wife)

        for task in wife_tasks:
            TaskShares.objects.get_or_create(task=task, user=instance.husband)
            
@receiver(post_save, sender=Tasks)
def share_task_between_couple(sender, instance, created, **kwargs):
    if created:
        # タスクが新しく作成された場合のみ処理を実行
        creator_couple = CoupleUser.objects.filter(Q(husband=instance.creator_user) | Q(wife=instance.creator_user)).first()
        assignment_couple = CoupleUser.objects.filter(Q(husband=instance.assignment_user) | Q(wife=instance.assignment_user)).first()

        if creator_couple and assignment_couple:
            # 作成者と担当者がどちらもカップルに紐づいている場合、タスクを共有
            TaskShares.objects.get_or_create(task=instance, user=creator_couple.husband)
            TaskShares.objects.get_or_create(task=instance, user=creator_couple.wife)
            TaskShares.objects.get_or_create(task=instance, user=assignment_couple.husband)
            TaskShares.objects.get_or_create(task=instance, user=assignment_couple.wife)           