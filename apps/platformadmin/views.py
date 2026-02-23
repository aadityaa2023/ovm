from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import PlatformAdmin
from .forms import AdminLoginForm
from .decorators import admin_required, superadmin_required
from voting.models import Voter, Election, Candidate, Vote, VoterVerification, State, Constituency


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

def login_view(request):
    """Admin login page."""
    if request.session.get('platform_admin_id'):
        return redirect('platformadmin:dashboard')

    form = AdminLoginForm()
    error = None

    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                admin = PlatformAdmin.objects.get(username=username, status='active')
                if admin.check_password(password):
                    request.session['platform_admin_id'] = admin.id
                    request.session['platform_admin_name'] = admin.full_name
                    request.session['platform_admin_role'] = admin.role
                    admin.update_last_login()
                    return redirect('platformadmin:dashboard')
                else:
                    error = 'Invalid username or password.'
            except PlatformAdmin.DoesNotExist:
                error = 'Invalid username or password.'

    return render(request, 'platformadmindashboard/login.html', {'form': form, 'error': error})


def logout_view(request):
    """Admin logout — clears the session keys."""
    for key in ['platform_admin_id', 'platform_admin_name', 'platform_admin_role']:
        request.session.pop(key, None)
    return redirect('platformadmin:login')


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

@admin_required
def dashboard_view(request):
    stats = {
        'total_voters': Voter.objects.count(),
        'verified_voters': Voter.objects.filter(is_verified=True).count(),
        'total_elections': Election.objects.count(),
        'live_elections': Election.objects.filter(status='live').count(),
        'total_votes': Vote.objects.count(),
        'total_candidates': Candidate.objects.count(),
        'total_states': State.objects.count(),
        'total_constituencies': Constituency.objects.count(),
    }
    recent_votes = Vote.objects.select_related('voter', 'election', 'candidate').order_by('-cast_at')[:10]
    recent_voters = Voter.objects.order_by('-created_at')[:5]
    elections = Election.objects.order_by('-start_date')[:5]

    return render(request, 'platformadmindashboard/dashboard.html', {
        'stats': stats,
        'recent_votes': recent_votes,
        'recent_voters': recent_voters,
        'elections': elections,
    })


# ─────────────────────────────────────────────
# Voters
# ─────────────────────────────────────────────

@admin_required
def voter_list(request):
    q = request.GET.get('q', '').strip()
    filter_verified = request.GET.get('verified', '')
    filter_voted = request.GET.get('voted', '')

    voters = Voter.objects.select_related('state', 'constituency').order_by('-created_at')

    if q:
        voters = voters.filter(Q(name__icontains=q) | Q(aadhaar_number__icontains=q) | Q(mobile_number__icontains=q))
    if filter_verified == '1':
        voters = voters.filter(is_verified=True)
    elif filter_verified == '0':
        voters = voters.filter(is_verified=False)
    if filter_voted == '1':
        voters = voters.filter(has_voted=True)
    elif filter_voted == '0':
        voters = voters.filter(has_voted=False)

    paginator = Paginator(voters, 20)
    page = request.GET.get('page', 1)
    voters_page = paginator.get_page(page)

    return render(request, 'platformadmindashboard/voters/list.html', {
        'voters': voters_page,
        'q': q,
        'filter_verified': filter_verified,
        'filter_voted': filter_voted,
        'total': paginator.count,
    })


@admin_required
def voter_detail(request, voter_id):
    voter = get_object_or_404(Voter.objects.select_related('state', 'constituency'), id=voter_id)
    verifications = voter.verifications.order_by('-attempted_at')[:20]
    votes = voter.votes.select_related('election', 'candidate').order_by('-cast_at')
    return render(request, 'platformadmindashboard/voters/detail.html', {
        'voter': voter,
        'verifications': verifications,
        'votes': votes,
    })


@admin_required
def voter_create(request):
    states = State.objects.all()
    constituencies = Constituency.objects.select_related('state').all()
    errors = {}

    if request.method == 'POST':
        data = request.POST
        errors = _validate_voter_form(data)
        if not errors:
            try:
                voter = Voter(
                    aadhaar_number=data['aadhaar_number'],
                    name=data['name'],
                    date_of_birth=data['date_of_birth'],
                    mobile_number=data['mobile_number'],
                    email=data.get('email') or None,
                    state_id=data['state'],
                    constituency_id=data['constituency'],
                    address=data['address'],
                    is_verified=bool(data.get('is_verified')),
                )
                if 'face_image' in request.FILES:
                    voter.face_image = request.FILES['face_image']
                voter.save()
                messages.success(request, f'Voter "{voter.name}" created successfully.')
                return redirect('platformadmin:voter_list')
            except Exception as e:
                errors['__all__'] = str(e)

    return render(request, 'platformadmindashboard/voters/form.html', {
        'action': 'Create',
        'states': states,
        'constituencies': constituencies,
        'errors': errors,
        'data': request.POST,
    })


@admin_required
def voter_edit(request, voter_id):
    voter = get_object_or_404(Voter, id=voter_id)
    states = State.objects.all()
    constituencies = Constituency.objects.select_related('state').all()
    errors = {}

    if request.method == 'POST':
        data = request.POST
        errors = _validate_voter_form(data, edit=True)
        if not errors:
            try:
                voter.name = data['name']
                voter.date_of_birth = data['date_of_birth']
                voter.mobile_number = data['mobile_number']
                voter.email = data.get('email') or None
                voter.state_id = data['state']
                voter.constituency_id = data['constituency']
                voter.address = data['address']
                voter.is_verified = bool(data.get('is_verified'))
                if 'face_image' in request.FILES:
                    voter.face_image = request.FILES['face_image']
                voter.save()
                messages.success(request, f'Voter "{voter.name}" updated successfully.')
                return redirect('platformadmin:voter_detail', voter_id=voter.id)
            except Exception as e:
                errors['__all__'] = str(e)

    return render(request, 'platformadmindashboard/voters/form.html', {
        'action': 'Edit',
        'voter': voter,
        'states': states,
        'constituencies': constituencies,
        'errors': errors,
        'data': request.POST or {
            'name': voter.name,
            'date_of_birth': voter.date_of_birth,
            'mobile_number': voter.mobile_number,
            'email': voter.email or '',
            'state': voter.state_id,
            'constituency': voter.constituency_id,
            'address': voter.address,
            'is_verified': voter.is_verified,
        },
    })


@admin_required
@require_POST
def voter_delete(request, voter_id):
    voter = get_object_or_404(Voter, id=voter_id)
    name = voter.name
    voter.delete()
    messages.success(request, f'Voter "{name}" deleted successfully.')
    return redirect('platformadmin:voter_list')


def _validate_voter_form(data, edit=False):
    errors = {}
    if not data.get('name'):
        errors['name'] = 'Name is required.'
    if not data.get('date_of_birth'):
        errors['date_of_birth'] = 'Date of birth is required.'
    if not data.get('mobile_number'):
        errors['mobile_number'] = 'Mobile number is required.'
    if not data.get('state'):
        errors['state'] = 'State is required.'
    if not data.get('constituency'):
        errors['constituency'] = 'Constituency is required.'
    if not data.get('address'):
        errors['address'] = 'Address is required.'
    if not edit and not data.get('aadhaar_number'):
        errors['aadhaar_number'] = 'Aadhaar number is required.'
    return errors


# ─────────────────────────────────────────────
# Elections
# ─────────────────────────────────────────────

@admin_required
def election_list(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    elections = Election.objects.annotate(vote_count=Count('votes'), candidate_count=Count('candidates'))

    if q:
        elections = elections.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if status_filter:
        elections = elections.filter(status=status_filter)

    elections = elections.order_by('-start_date')
    paginator = Paginator(elections, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'platformadmindashboard/elections/list.html', {
        'elections': page_obj,
        'q': q,
        'status_filter': status_filter,
        'total': paginator.count,
        'status_choices': Election.STATUS_CHOICES,
    })


@admin_required
def election_create(request):
    errors = {}
    if request.method == 'POST':
        errors = _validate_election_form(request.POST)
        if not errors:
            try:
                Election.objects.create(
                    title=request.POST['title'],
                    description=request.POST['description'],
                    election_type=request.POST['election_type'],
                    status=request.POST['status'],
                    start_date=request.POST['start_date'],
                    end_date=request.POST['end_date'],
                )
                messages.success(request, 'Election created successfully.')
                return redirect('platformadmin:election_list')
            except Exception as e:
                errors['__all__'] = str(e)

    return render(request, 'platformadmindashboard/elections/form.html', {
        'action': 'Create',
        'election_types': Election.ELECTION_TYPES,
        'status_choices': Election.STATUS_CHOICES,
        'errors': errors,
        'data': request.POST,
    })


@admin_required
def election_edit(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    errors = {}

    if request.method == 'POST':
        errors = _validate_election_form(request.POST)
        if not errors:
            try:
                election.title = request.POST['title']
                election.description = request.POST['description']
                election.election_type = request.POST['election_type']
                election.status = request.POST['status']
                election.start_date = request.POST['start_date']
                election.end_date = request.POST['end_date']
                election.save()
                messages.success(request, 'Election updated successfully.')
                return redirect('platformadmin:election_list')
            except Exception as e:
                errors['__all__'] = str(e)

    return render(request, 'platformadmindashboard/elections/form.html', {
        'action': 'Edit',
        'election': election,
        'election_types': Election.ELECTION_TYPES,
        'status_choices': Election.STATUS_CHOICES,
        'errors': errors,
        'data': request.POST or {
            'title': election.title,
            'description': election.description,
            'election_type': election.election_type,
            'status': election.status,
            'start_date': election.start_date.strftime('%Y-%m-%dT%H:%M'),
            'end_date': election.end_date.strftime('%Y-%m-%dT%H:%M'),
        },
    })


@admin_required
@require_POST
def election_delete(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    title = election.title
    election.delete()
    messages.success(request, f'Election "{title}" deleted successfully.')
    return redirect('platformadmin:election_list')


def _validate_election_form(data):
    errors = {}
    for field in ['title', 'description', 'election_type', 'status', 'start_date', 'end_date']:
        if not data.get(field):
            errors[field] = f'{field.replace("_", " ").title()} is required.'
    return errors


# ─────────────────────────────────────────────
# Candidates
# ─────────────────────────────────────────────

@admin_required
def candidate_list(request):
    q = request.GET.get('q', '').strip()
    election_filter = request.GET.get('election', '')

    candidates = Candidate.objects.select_related('election', 'constituency').annotate(vote_count=Count('votes'))

    if q:
        candidates = candidates.filter(Q(name__icontains=q) | Q(party_name__icontains=q))
    if election_filter:
        candidates = candidates.filter(election_id=election_filter)

    candidates = candidates.order_by('election', 'name')
    paginator = Paginator(candidates, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'platformadmindashboard/candidates/list.html', {
        'candidates': page_obj,
        'q': q,
        'election_filter': election_filter,
        'elections': Election.objects.all().order_by('-start_date'),
        'total': paginator.count,
    })


@admin_required
def candidate_create(request):
    errors = {}
    if request.method == 'POST':
        errors = _validate_candidate_form(request.POST)
        if not errors:
            try:
                candidate = Candidate(
                    name=request.POST['name'],
                    party_name=request.POST['party_name'],
                    election_id=request.POST['election'],
                    constituency_id=request.POST['constituency'],
                    manifesto=request.POST.get('manifesto', ''),
                )
                if 'photo' in request.FILES:
                    candidate.photo = request.FILES['photo']
                if 'party_symbol' in request.FILES:
                    candidate.party_symbol = request.FILES['party_symbol']
                candidate.save()
                messages.success(request, f'Candidate "{candidate.name}" added successfully.')
                return redirect('platformadmin:candidate_list')
            except Exception as e:
                errors['__all__'] = str(e)

    return render(request, 'platformadmindashboard/candidates/form.html', {
        'action': 'Create',
        'elections': Election.objects.all().order_by('-start_date'),
        'constituencies': Constituency.objects.select_related('state').all(),
        'errors': errors,
        'data': request.POST,
    })


@admin_required
def candidate_edit(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    errors = {}

    if request.method == 'POST':
        errors = _validate_candidate_form(request.POST)
        if not errors:
            try:
                candidate.name = request.POST['name']
                candidate.party_name = request.POST['party_name']
                candidate.election_id = request.POST['election']
                candidate.constituency_id = request.POST['constituency']
                candidate.manifesto = request.POST.get('manifesto', '')
                if 'photo' in request.FILES:
                    candidate.photo = request.FILES['photo']
                if 'party_symbol' in request.FILES:
                    candidate.party_symbol = request.FILES['party_symbol']
                candidate.save()
                messages.success(request, f'Candidate "{candidate.name}" updated successfully.')
                return redirect('platformadmin:candidate_list')
            except Exception as e:
                errors['__all__'] = str(e)

    return render(request, 'platformadmindashboard/candidates/form.html', {
        'action': 'Edit',
        'candidate': candidate,
        'elections': Election.objects.all().order_by('-start_date'),
        'constituencies': Constituency.objects.select_related('state').all(),
        'errors': errors,
        'data': request.POST or {
            'name': candidate.name,
            'party_name': candidate.party_name,
            'election': candidate.election_id,
            'constituency': candidate.constituency_id,
            'manifesto': candidate.manifesto,
        },
    })


@admin_required
@require_POST
def candidate_delete(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    name = candidate.name
    candidate.delete()
    messages.success(request, f'Candidate "{name}" deleted.')
    return redirect('platformadmin:candidate_list')


def _validate_candidate_form(data):
    errors = {}
    for field in ['name', 'party_name', 'election', 'constituency']:
        if not data.get(field):
            errors[field] = f'{field.replace("_", " ").title()} is required.'
    return errors


# ─────────────────────────────────────────────
# Votes (read-only)
# ─────────────────────────────────────────────

@admin_required
def vote_list(request):
    q = request.GET.get('q', '').strip()
    election_filter = request.GET.get('election', '')

    votes = Vote.objects.select_related('voter', 'election', 'candidate')

    if q:
        votes = votes.filter(Q(voter__aadhaar_number__icontains=q) | Q(blockchain_hash__icontains=q))
    if election_filter:
        votes = votes.filter(election_id=election_filter)

    votes = votes.order_by('-cast_at')
    paginator = Paginator(votes, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'platformadmindashboard/votes/list.html', {
        'votes': page_obj,
        'q': q,
        'election_filter': election_filter,
        'elections': Election.objects.all().order_by('-start_date'),
        'total': paginator.count,
    })


# ─────────────────────────────────────────────
# Admin Account Management
# ─────────────────────────────────────────────

@superadmin_required
def admin_user_list(request):
    admins = PlatformAdmin.objects.all()
    return render(request, 'platformadmindashboard/admins/list.html', {'admins': admins})


@superadmin_required
def admin_user_create(request):
    errors = {}
    if request.method == 'POST':
        data = request.POST
        errors = _validate_admin_form(data)
        if not errors:
            try:
                admin = PlatformAdmin(
                    username=data['username'],
                    full_name=data['full_name'],
                    email=data['email'],
                    role=data.get('role', 'admin'),
                    status=data.get('status', 'active'),
                )
                admin.set_password(data['password'])
                admin.save()
                messages.success(request, f'Admin "{admin.username}" created successfully.')
                return redirect('platformadmin:admin_user_list')
            except Exception as e:
                errors['__all__'] = str(e)

    return render(request, 'platformadmindashboard/admins/form.html', {
        'action': 'Create',
        'role_choices': PlatformAdmin.ROLE_CHOICES,
        'status_choices': PlatformAdmin.STATUS_CHOICES,
        'errors': errors,
        'data': request.POST,
    })


@superadmin_required
def admin_user_edit(request, admin_id):
    admin = get_object_or_404(PlatformAdmin, id=admin_id)
    errors = {}

    if request.method == 'POST':
        data = request.POST
        if not data.get('full_name'):
            errors['full_name'] = 'Full name is required.'
        if not data.get('email'):
            errors['email'] = 'Email is required.'
        if not errors:
            try:
                admin.full_name = data['full_name']
                admin.email = data['email']
                admin.role = data.get('role', admin.role)
                admin.status = data.get('status', admin.status)
                if data.get('password'):
                    admin.set_password(data['password'])
                admin.save()
                messages.success(request, 'Admin account updated.')
                return redirect('platformadmin:admin_user_list')
            except Exception as e:
                errors['__all__'] = str(e)

    return render(request, 'platformadmindashboard/admins/form.html', {
        'action': 'Edit',
        'admin_obj': admin,
        'role_choices': PlatformAdmin.ROLE_CHOICES,
        'status_choices': PlatformAdmin.STATUS_CHOICES,
        'errors': errors,
        'data': request.POST or {
            'full_name': admin.full_name,
            'email': admin.email,
            'role': admin.role,
            'status': admin.status,
        },
    })


@superadmin_required
@require_POST
def admin_user_delete(request, admin_id):
    admin = get_object_or_404(PlatformAdmin, id=admin_id)
    if admin.id == request.session.get('platform_admin_id'):
        messages.error(request, 'You cannot delete your own account.')
        return redirect('platformadmin:admin_user_list')
    username = admin.username
    admin.delete()
    messages.success(request, f'Admin "{username}" deleted.')
    return redirect('platformadmin:admin_user_list')


def _validate_admin_form(data):
    errors = {}
    for field in ['username', 'full_name', 'email', 'password']:
        if not data.get(field):
            errors[field] = f'{field.replace("_", " ").title()} is required.'
    return errors


# ─────────────────────────────────────────────
# AJAX — constituencies by state
# ─────────────────────────────────────────────

@admin_required
def api_constituencies_by_state(request, state_id):
    constituencies = list(Constituency.objects.filter(state_id=state_id).values('id', 'name', 'constituency_code'))
    return JsonResponse({'constituencies': constituencies})
