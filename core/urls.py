from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', MyLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='roadmap_list'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify'),

    path('profile/', ProfileView.as_view(), name='profile'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('profile/password/', auth_views.PasswordChangeView.as_view(template_name='profile/password_change.html',success_url=reverse_lazy('password_change')), name='password_change'),
    path('submissions/', SubmissionListView.as_view(), name='submission_list'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('user/<str:username>/', UserProfileDetailView.as_view(), name='user_profile'),


    path('',RoadmapListView.as_view(),name='roadmap_list'),
    path('roadmap/<int:pk>/',RoadmapDetailView.as_view(),name='roadmap_detail'),
    path('node/<int:pk>/', NodeDetailView.as_view(), name='node_detail'),

    path('api/generate-subtopic/<int:pk>/', GenerateSubtopicView.as_view(), name='generate_subtopic_api'),
    path('subtopic/<int:pk>/', SubtopicDetailView.as_view(), name='subtopic_detail'),
    path('node/<int:node_id>/check/', CheckSubmissionView.as_view(), name='check_submission'),
]