from django.urls import path
from . import views

app_name = 'platformadmin'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Voters
    path('voters/', views.voter_list, name='voter_list'),
    path('voters/create/', views.voter_create, name='voter_create'),
    path('voters/<int:voter_id>/', views.voter_detail, name='voter_detail'),
    path('voters/<int:voter_id>/edit/', views.voter_edit, name='voter_edit'),
    path('voters/<int:voter_id>/delete/', views.voter_delete, name='voter_delete'),

    # Elections
    path('elections/', views.election_list, name='election_list'),
    path('elections/create/', views.election_create, name='election_create'),
    path('elections/<int:election_id>/edit/', views.election_edit, name='election_edit'),
    path('elections/<int:election_id>/delete/', views.election_delete, name='election_delete'),

    # Candidates
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/create/', views.candidate_create, name='candidate_create'),
    path('candidates/<int:candidate_id>/edit/', views.candidate_edit, name='candidate_edit'),
    path('candidates/<int:candidate_id>/delete/', views.candidate_delete, name='candidate_delete'),

    # Votes (read-only)
    path('votes/', views.vote_list, name='vote_list'),

    # Admin accounts (superadmin only)
    path('admins/', views.admin_user_list, name='admin_user_list'),
    path('admins/create/', views.admin_user_create, name='admin_user_create'),
    path('admins/<int:admin_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('admins/<int:admin_id>/delete/', views.admin_user_delete, name='admin_user_delete'),

    # AJAX
    path('api/constituencies/<int:state_id>/', views.api_constituencies_by_state, name='api_constituencies'),
]
