from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import hashlib


class State(models.Model):
    """Indian States"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True)  # e.g., 'MH' for Maharashtra
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Constituency(models.Model):
    """Electoral Constituencies"""
    name = models.CharField(max_length=200)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='constituencies')
    constituency_code = models.CharField(max_length=10, unique=True)
    total_voters = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['state', 'name']
        verbose_name_plural = 'Constituencies'
    
    def __str__(self):
        return f"{self.name}, {self.state.name}"


class Voter(models.Model):
    """Voter model with biometric data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    aadhaar_number = models.CharField(max_length=12, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    mobile_number = models.CharField(max_length=10)
    email = models.EmailField(blank=True, null=True)
    
    # Address
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='voters')
    constituency = models.ForeignKey(Constituency, on_delete=models.PROTECT, related_name='voters')
    address = models.TextField()
    
    # Biometric data
    face_image = models.ImageField(upload_to='voter_faces/', null=True, blank=True)
    face_encoding = models.BinaryField(null=True, blank=True)  # Stores numpy array as binary
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_attempts = models.IntegerField(default=0)
    
    # Voting status
    has_voted = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.aadhaar_number})"
    
    def mark_as_verified(self):
        """Mark voter as verified"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()


class Election(models.Model):
    """Election Events"""
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ELECTION_TYPES = [
        ('general', 'General Election'),
        ('state', 'State Assembly'),
        ('local', 'Local Body'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    election_type = models.CharField(max_length=20, choices=ELECTION_TYPES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Blockchain reference
    blockchain_contract_address = models.CharField(max_length=42, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    def is_active(self):
        """Check if election is currently active"""
        now = timezone.now()
        return self.status == 'live' and self.start_date <= now <= self.end_date


class Candidate(models.Model):
    """Candidates in Elections"""
    name = models.CharField(max_length=200)
    party_name = models.CharField(max_length=200)
    party_symbol = models.ImageField(upload_to='party_symbols/', null=True, blank=True)
    
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    constituency = models.ForeignKey(Constituency, on_delete=models.CASCADE, related_name='candidates')
    
    manifesto = models.TextField(blank=True)
    photo = models.ImageField(upload_to='candidate_photos/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['election', 'constituency', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.party_name})"
    
    def get_vote_count(self):
        """Get total votes for this candidate"""
        return self.votes.count()


class Vote(models.Model):
    """Vote Records"""
    voter = models.ForeignKey(Voter, on_delete=models.PROTECT, related_name='votes')
    election = models.ForeignKey(Election, on_delete=models.PROTECT, related_name='votes')
    candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT, related_name='votes')
    
    # Blockchain data
    blockchain_hash = models.CharField(max_length=66, unique=True, db_index=True)
    transaction_hash = models.CharField(max_length=66, unique=True)
    
    # Metadata
    cast_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-cast_at']
        unique_together = ['voter', 'election']  # One vote per election per voter
    
    def __str__(self):
        return f"Vote by {self.voter.aadhaar_number} in {self.election.title}"
    
    def generate_receipt_hash(self):
        """Generate a receipt hash for the voter"""
        data = f"{self.voter.aadhaar_number}{self.election.id}{self.cast_at}"
        return hashlib.sha256(data.encode()).hexdigest()


class VoterVerification(models.Model):
    """Verification Attempts Log"""
    VERIFICATION_TYPES = [
        ('face', 'Face Recognition'),
        ('liveness', 'Liveness Detection'),
        ('duplicate', 'Duplicate Check'),
    ]
    
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='verifications')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    success = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-attempted_at']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.verification_type} - {status} ({self.attempted_at})"



