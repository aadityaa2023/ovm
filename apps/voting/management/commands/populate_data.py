from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from voting.models import State, Constituency, Election, Candidate, Voter


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating database with sample data...')
        
        # Create States
        states_data = [
            {'name': 'Maharashtra', 'code': 'MH'},
            {'name': 'Karnataka', 'code': 'KA'},
            {'name': 'Tamil Nadu', 'code': 'TN'},
            {'name': 'Gujarat', 'code': 'GJ'},
            {'name': 'Delhi', 'code': 'DL'},
        ]
        
        states = {}
        for state_data in states_data:
            state, created = State.objects.get_or_create(**state_data)
            states[state.code] = state
            if created:
                self.stdout.write(f'Created state: {state.name}')
        
        # Create Constituencies
        constituencies_data = [
            {'name': 'Mumbai North', 'state': states['MH'], 'constituency_code': 'MH01'},
            {'name': 'Mumbai South', 'state': states['MH'], 'constituency_code': 'MH02'},
            {'name': 'Pune', 'state': states['MH'], 'constituency_code': 'MH03'},
            {'name': 'Bangalore North', 'state': states['KA'], 'constituency_code': 'KA01'},
            {'name': 'Bangalore South', 'state': states['KA'], 'constituency_code': 'KA02'},
            {'name': 'Chennai Central', 'state': states['TN'], 'constituency_code': 'TN01'},
            {'name': 'Ahmedabad East', 'state': states['GJ'], 'constituency_code': 'GJ01'},
            {'name': 'New Delhi', 'state': states['DL'], 'constituency_code': 'DL01'},
        ]
        
        constituencies = {}
        for const_data in constituencies_data:
            const, created = Constituency.objects.get_or_create(**const_data)
            constituencies[const.constituency_code] = const
            if created:
                self.stdout.write(f'Created constituency: {const.name}')
        
        # Create Elections
        now = timezone.now()
        elections_data = [
            {
                'title': '2026 General Election',
                'description': 'National General Election for Lok Sabha',
                'election_type': 'general',
                'status': 'live',
                'start_date': now - timedelta(days=1),
                'end_date': now + timedelta(days=7),
            },
            {
                'title': 'Maharashtra State Assembly Election',
                'description': 'State Assembly Election for Maharashtra',
                'election_type': 'state',
                'status': 'upcoming',
                'start_date': now + timedelta(days=30),
                'end_date': now + timedelta(days=37),
            },
        ]
        
        elections = []
        for elec_data in elections_data:
            elec, created = Election.objects.get_or_create(
                title=elec_data['title'],
                defaults=elec_data
            )
            elections.append(elec)
            if created:
                self.stdout.write(f'Created election: {elec.title}')
        
        # Create Candidates for General Election
        general_election = elections[0]
        candidates_data = [
            # Mumbai North
            {'name': 'Rajesh Kumar', 'party_name': 'Indian National Congress', 'constituency': constituencies['MH01']},
            {'name': 'Priya Sharma', 'party_name': 'Bharatiya Janata Party', 'constituency': constituencies['MH01']},
            {'name': 'Amit Patel', 'party_name': 'Aam Aadmi Party', 'constituency': constituencies['MH01']},
            
            # Mumbai South
            {'name': 'Sunita Desai', 'party_name': 'Indian National Congress', 'constituency': constituencies['MH02']},
            {'name': 'Vikram Singh', 'party_name': 'Bharatiya Janata Party', 'constituency': constituencies['MH02']},
            
            # Bangalore North
            {'name': 'Ramesh Rao', 'party_name': 'Indian National Congress', 'constituency': constituencies['KA01']},
            {'name': 'Lakshmi Iyer', 'party_name': 'Bharatiya Janata Party', 'constituency': constituencies['KA01']},
            
            # Delhi
            {'name': 'Arvind Kejriwal', 'party_name': 'Aam Aadmi Party', 'constituency': constituencies['DL01']},
            {'name': 'Manoj Tiwari', 'party_name': 'Bharatiya Janata Party', 'constituency': constituencies['DL01']},
        ]
        
        for cand_data in candidates_data:
            cand_data['election'] = general_election
            cand, created = Candidate.objects.get_or_create(**cand_data)
            if created:
                self.stdout.write(f'Created candidate: {cand.name} ({cand.constituency.name})')
        
        # Create sample voters
        voters_data = [
            {
                'aadhaar_number': '123456789012',
                'name': 'Test Voter 1',
                'date_of_birth': '1990-01-01',
                'mobile_number': '9876543210',
                'email': 'voter1@example.com',
                'state': states['MH'],
                'constituency': constituencies['MH01'],
                'address': 'Test Address 1, Mumbai',
                'is_verified': True,
            },
            {
                'aadhaar_number': '123456789013',
                'name': 'Test Voter 2',
                'date_of_birth': '1985-05-15',
                'mobile_number': '9876543211',
                'email': 'voter2@example.com',
                'state': states['KA'],
                'constituency': constituencies['KA01'],
                'address': 'Test Address 2, Bangalore',
                'is_verified': True,
            },
        ]
        
        for voter_data in voters_data:
            voter, created = Voter.objects.get_or_create(
                aadhaar_number=voter_data['aadhaar_number'],
                defaults=voter_data
            )
            if created:
                self.stdout.write(f'Created voter: {voter.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))
