"""
Blockchain Service for Voting System

This module provides blockchain integration for secure vote storage.
For development, we use a simulated blockchain.
For production, this can be connected to Ethereum, Polygon, or Hyperledger.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, List
import secrets


class Block:
    """Represents a block in the blockchain"""
    
    def __init__(self, index: int, timestamp: str, data: dict, previous_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int = 2):
        """Mine the block with proof of work"""
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def to_dict(self) -> dict:
        """Convert block to dictionary"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }


class VotingBlockchain:
    """Blockchain for storing votes"""
    
    def __init__(self):
        self.chain: List[Block] = []
        self.difficulty = 2
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = Block(0, str(datetime.now()), {
            'type': 'genesis',
            'message': 'Genesis Block - Matdaan Voting System'
        }, '0')
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1]
    
    def add_block(self, data: dict) -> Block:
        """Add a new block to the chain"""
        new_block = Block(
            index=len(self.chain),
            timestamp=str(datetime.now()),
            data=data,
            previous_hash=self.get_latest_block().hash
        )
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        return new_block
    
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if hash is correct
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if previous hash matches
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Find block by hash"""
        for block in self.chain:
            if block.hash == block_hash:
                return block
        return None
    
    def get_blocks_by_election(self, election_id: int) -> List[Block]:
        """Get all blocks for a specific election"""
        blocks = []
        for block in self.chain:
            if block.data.get('type') == 'vote' and block.data.get('election_id') == election_id:
                blocks.append(block)
        return blocks


class BlockchainService:
    """Service for blockchain operations"""
    
    def __init__(self):
        self.blockchain = VotingBlockchain()
    
    def cast_vote_to_blockchain(self, voter_id: str, election_id: int, candidate_id: int) -> Dict:
        """
        Record a vote on the blockchain
        
        Args:
            voter_id: Hashed voter ID (for anonymity)
            election_id: Election ID
            candidate_id: Candidate ID (encrypted)
            
        Returns:
            dict with transaction details
        """
        # Create vote data (candidate choice is hashed for privacy)
        vote_data = {
            'type': 'vote',
            'voter_hash': hashlib.sha256(voter_id.encode()).hexdigest(),
            'election_id': election_id,
            'candidate_hash': hashlib.sha256(str(candidate_id).encode()).hexdigest(),
            'timestamp': str(datetime.now()),
            'transaction_id': secrets.token_hex(16)
        }
        
        # Add block to blockchain
        block = self.blockchain.add_block(vote_data)
        
        return {
            'success': True,
            'block_hash': block.hash,
            'transaction_hash': vote_data['transaction_id'],
            'block_index': block.index,
            'timestamp': block.timestamp
        }
    
    def verify_vote(self, block_hash: str) -> Dict:
        """
        Verify a vote exists on the blockchain
        
        Args:
            block_hash: Hash of the block containing the vote
            
        Returns:
            dict with verification results
        """
        block = self.blockchain.get_block_by_hash(block_hash)
        
        if block is None:
            return {
                'verified': False,
                'message': 'Vote not found on blockchain'
            }
        
        # Verify blockchain integrity
        is_valid = self.blockchain.is_chain_valid()
        
        return {
            'verified': True,
            'is_valid_chain': is_valid,
            'block_index': block.index,
            'timestamp': block.timestamp,
            'data': block.data,
            'message': 'Vote verified on blockchain'
        }
    
    def get_election_results(self, election_id: int) -> Dict:
        """
        Get aggregated results for an election from blockchain
        
        Args:
            election_id: Election ID
            
        Returns:
            dict with vote counts
        """
        blocks = self.blockchain.get_blocks_by_election(election_id)
        
        # Count votes by candidate hash
        vote_counts = {}
        for block in blocks:
            candidate_hash = block.data.get('candidate_hash')
            if candidate_hash:
                vote_counts[candidate_hash] = vote_counts.get(candidate_hash, 0) + 1
        
        return {
            'election_id': election_id,
            'total_votes': len(blocks),
            'vote_distribution': vote_counts,
            'blockchain_verified': self.blockchain.is_chain_valid()
        }
    
    def has_voter_voted(self, voter_id: str, election_id: int) -> bool:
        """
        Check if a voter has already voted in an election
        
        Args:
            voter_id: Voter ID
            election_id: Election ID
            
        Returns:
            bool indicating if voter has voted
        """
        voter_hash = hashlib.sha256(voter_id.encode()).hexdigest()
        blocks = self.blockchain.get_blocks_by_election(election_id)
        
        for block in blocks:
            if block.data.get('voter_hash') == voter_hash:
                return True
        
        return False
    
    def get_blockchain_stats(self) -> Dict:
        """Get blockchain statistics"""
        return {
            'total_blocks': len(self.blockchain.chain),
            'is_valid': self.blockchain.is_chain_valid(),
            'latest_block_hash': self.blockchain.get_latest_block().hash,
            'difficulty': self.blockchain.difficulty
        }
    
    def export_blockchain(self) -> List[dict]:
        """Export entire blockchain as JSON"""
        return [block.to_dict() for block in self.blockchain.chain]


# Singleton instance
blockchain_service = BlockchainService()
