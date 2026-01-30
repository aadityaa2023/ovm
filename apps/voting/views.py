from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.files.base import ContentFile
import json
import base64

from .models import Voter, Election, Candidate, Vote, VoterVerification, Constituency, State
from ai_verification.verification_service import verification_service
from blockchain.blockchain_service import blockchain_service


def index(request):
    """Landing page with login"""
    # Get active elections
    active_elections = Election.objects.filter(status='live')
    
    context = {
        'active_elections': active_elections
    }
    return render(request, 'index.html', context)


@csrf_exempt
def api_verify_login(request):
    """API endpoint for Aadhaar-based login with face verification"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        aadhaar = data.get('aadhaar_number')
        
        if not aadhaar:
            return JsonResponse({'success': False, 'message': 'Aadhaar number required'})
        
        # Get voter
        try:
            voter = Voter.objects.get(aadhaar_number=aadhaar)
        except Voter.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Voter not found'})
        
        if not voter.is_verified:
            return JsonResponse({'success': False, 'message': 'Voter not verified'})
        
        # Create session
        request.session['voter_id'] = voter.id
        request.session['voter_aadhaar'] = voter.aadhaar_number
        request.session['voter_name'] = voter.name
        
        return JsonResponse({
            'success': True,
            'message': 'Login successful',
            'voter_name': voter.name,
            'voter_id': voter.aadhaar_number
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Login failed: {str(e)}'
        })


def dashboard(request):
    """Voter dashboard"""
    voter_id = request.session.get('voter_id')
    if not voter_id:
        return redirect('index')
    
    voter = get_object_or_404(Voter, id=voter_id)
    
    # Get active elections for voter's constituency
    active_elections = Election.objects.filter(
        status='live',
        candidates__constituency=voter.constituency
    ).distinct()
    
    # Check which elections voter has voted in
    voted_elections = Vote.objects.filter(voter=voter).values_list('election_id', flat=True)
    
    context = {
        'voter': voter,
        'active_elections': active_elections,
        'voted_elections': list(voted_elections)
    }
    return render(request, 'dashboard.html', context)


def vote_page(request, election_id):
    """Voting page for specific election"""
    voter_id = request.session.get('voter_id')
    if not voter_id:
        return redirect('index')
    
    voter = get_object_or_404(Voter, id=voter_id)
    election = get_object_or_404(Election, id=election_id)
    
    # Check if election is active
    if not election.is_active():
        return redirect('dashboard')
    
    # Check if voter has already voted
    if Vote.objects.filter(voter=voter, election=election).exists():
        return redirect('dashboard')
    
    # Get candidates for voter's constituency
    candidates = Candidate.objects.filter(
        election=election,
        constituency=voter.constituency
    )
    
    context = {
        'election': election,
        'candidates': candidates,
        'voter': voter
    }
    return render(request, 'vote.html', context)


@csrf_exempt
def api_cast_vote(request):
    """API endpoint to cast vote"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        voter_id = request.session.get('voter_id')
        if not voter_id:
            return JsonResponse({'success': False, 'message': 'Not logged in'})
        
        data = json.loads(request.body)
        election_id = data.get('election_id')
        candidate_id = data.get('candidate_id')
        
        voter = Voter.objects.get(id=voter_id)
        election = Election.objects.get(id=election_id)
        candidate = Candidate.objects.get(id=candidate_id)
        
        # Validate
        if not election.is_active():
            return JsonResponse({'success': False, 'message': 'Election is not active'})
        
        if Vote.objects.filter(voter=voter, election=election).exists():
            return JsonResponse({'success': False, 'message': 'You have already voted'})
        
        if candidate.constituency != voter.constituency:
            return JsonResponse({'success': False, 'message': 'Invalid candidate for your constituency'})
        
        # Record vote on blockchain
        blockchain_result = blockchain_service.cast_vote_to_blockchain(
            voter_id=voter.aadhaar_number,
            election_id=election.id,
            candidate_id=candidate.id
        )
        
        if not blockchain_result['success']:
            return JsonResponse({'success': False, 'message': 'Blockchain recording failed'})
        
        # Create vote record
        vote = Vote.objects.create(
            voter=voter,
            election=election,
            candidate=candidate,
            blockchain_hash=blockchain_result['block_hash'],
            transaction_hash=blockchain_result['transaction_hash'],
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Mark voter as voted
        voter.has_voted = True
        voter.save()
        
        # Generate receipt
        receipt_hash = vote.generate_receipt_hash()
        
        return JsonResponse({
            'success': True,
            'message': 'Vote cast successfully',
            'blockchain_hash': blockchain_result['block_hash'],
            'transaction_hash': blockchain_result['transaction_hash'],
            'receipt_hash': receipt_hash,
            'timestamp': vote.cast_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to cast vote: {str(e)}'
        })


def logout_view(request):
    """Logout user"""
    request.session.flush()
    return redirect('index')
