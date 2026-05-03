
from django.urls import path
from .views import *
urlpatterns = [
    # ... существующие
    path('', ChallengeListView.as_view(), name='challenge_list'),
    path('<int:pk>/', ChallengeDetailView.as_view(), name='challenge_detail'),
    path('<int:pk>/submit/', ChallengeSubmitView.as_view(), name='challenge_submit'),
    path('generate/', GenerateChallengeView.as_view(), name='generate_challenge'),
]