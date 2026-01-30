from django.contrib import admin
from .models import State, Constituency, Voter, Election, Candidate, Vote, VoterVerification, Admin


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']


@admin.register(Constituency)
class ConstituencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'constituency_code', 'total_voters']
    list_filter = ['state']
    search_fields = ['name', 'constituency_code']


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ['name', 'aadhaar_number', 'constituency', 'is_verified', 'has_voted', 'created_at']
    list_filter = ['is_verified', 'has_voted', 'state', 'constituency']
    search_fields = ['name', 'aadhaar_number', 'mobile_number']
    readonly_fields = ['face_encoding', 'verified_at', 'created_at', 'updated_at']


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'election_type', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'election_type']
    search_fields = ['title', 'description']
    date_hierarchy = 'start_date'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'party_name', 'election', 'constituency']
    list_filter = ['election', 'constituency']
    search_fields = ['name', 'party_name']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'election', 'candidate', 'cast_at', 'blockchain_hash']
    list_filter = ['election', 'cast_at']
    search_fields = ['blockchain_hash', 'transaction_hash']
    readonly_fields = ['blockchain_hash', 'transaction_hash', 'cast_at', 'ip_address']


@admin.register(VoterVerification)
class VoterVerificationAdmin(admin.ModelAdmin):
    list_display = ['voter', 'verification_type', 'success', 'confidence_score', 'attempted_at']
    list_filter = ['verification_type', 'success', 'attempted_at']
    search_fields = ['voter__name', 'voter__aadhaar_number']
    readonly_fields = ['attempted_at']


@admin.register(Admin)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'full_name', 'email', 'role', 'status', 'created_at']
    list_filter = ['role', 'status']
    search_fields = ['username', 'full_name', 'email']
