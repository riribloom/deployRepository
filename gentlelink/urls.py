from django.urls import path
from . import views
from .views import delete_task_view, task_detail_view, edit_task_view, task_search_view, user_settings, calendar_view
from .views import notification_view, password_change_view, MemoDetailView, EditMemoView, share_task_with_partner, task_list_view, couple_registration_view, couple_registration_success_view, settings_view
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.welcome_view, name='welcome'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('home/', views.home_view, name='home'),
    path('task-search/', task_search_view, name='task_search'),
    path('logout/', views.logout_view, name='logout'),  
    path('task-list/', views.task_list_view, name='task_list'),
    path('create-task/', views.create_task_view, name='create_task'),
    path('task-detail/<int:task_id>/', task_detail_view, name='task_detail'),
    path('edit-task/<int:task_id>/', views.edit_task_view, name='edit_task'),
    path('delete-task/<int:task_id>/', delete_task_view, name='delete_task'),  
    path('user_settings/', views.user_settings, name='user_settings'),
    path('password_change/', password_change_view, name='password_change'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('notification/', views.notification_view, name='notification'),
    path('memo_detail/create/', MemoDetailView.as_view(), name='memo_create'),
    path('memo_edit/<int:id>/', EditMemoView.as_view(), name='memo_edit'),
    path('share_task/<int:task_id>/', share_task_with_partner, name='share_task'),
    path('couple_registration/', couple_registration_view, name='couple_registration'),
    path('couple_registration_success/', couple_registration_success_view, name='couple_registration_success'),
    path('settings/', settings_view, name='settings'),
]

# 開発環境でのみ静的ファイルを提供する設定
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)