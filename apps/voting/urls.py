from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vote/<int:election_id>/', views.vote_page, name='vote_page'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints
    path('api/verify-login/', views.api_verify_login, name='api_verify_login'),
    path('api/cast-vote/', views.api_cast_vote, name='api_cast_vote'),
]
