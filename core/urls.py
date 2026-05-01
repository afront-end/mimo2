from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import *

urlpatterns = [
    path('login/', MyLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='roadmap_list'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),


    path('',RoadmapListView.as_view(),name='roadmap_list'),
    path('roadmap/<int:pk>/',RoadmapDetailView.as_view(),name='roadmap_detail'),
    path('node/<int:pk>/', NodeDetailView.as_view(), name='node_detail'),

    path('api/generate-subtopic/<int:pk>/', GenerateSubtopicView.as_view(), name='generate_subtopic_api'),
]