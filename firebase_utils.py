"""
Firebase State Management Utilities
Core Tenet: State is the only shared memory between cellular agents
"""
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from google.cloud.firestore_v1.base_transaction import Transaction
import logging
from config import config, logger

class FirebaseStateManager:
    """Atomic state management for distributed agent coordination"""
    
    def __init__(self):
        self.db = config.get_firestore_client()
        self.logger = logging.getLogger(__name__)
    
    def atomic_update(self, 
                     collection: str, 
                     doc_id: str, 
                     update_data: Dict[str, Any],
                     transaction: Optional[Transaction] = None) -> bool:
        """
        Perform atomic update with optimistic concurrency control
        Returns True if successful, False if conflict
        """
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            
            def update_in_transaction(transaction: Transaction):
                snapshot = transaction.get(doc_ref)
                current_data = snapshot.to_dict() if snapshot.exists else {}
                
                # Merge update, preserving existing fields unless specified for deletion
                for key, value in update_data.items():
                    if value is None:  # Delete field
                        current_data.pop(key, None)
                    else:
                        current_data[key] = value
                
                # Add metadata
                current_data['_updated_at'] = firestore.SERVER_TIMESTAMP
                current_data['_version'] = (current_data.get('_version', 0) + 1)
                
                transaction.set(doc_ref, current_data)
                return True
            
            if transaction:
                return update_in_transaction(transaction)
            else:
                return self.db.transaction(update_in_transaction)
                
        except Exception as e:
            self.logger.error(f"Atomic update failed for {collection}/{doc_id}: {e}")
            return False
    
    def create_opportunity_signal(self, 
                                 opportunity_data: Dict[str, Any],
                                 source_verification: List[str]) -> Optional[str]:
        """
        Create an encrypted opportunity signal with proof-of-uniqueness
        Returns opportunity_hash if successful
        """
        try:
            # Generate unique hash from opportunity data
            data_str = json.dumps(opportunity_data, sort_keys=True)
            opportunity_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
            
            # Check for duplicate opportunities
            existing = self.db.collection(config.COLLECTIONS['opportunities'])\
                .where('opportunity_hash', '==', opportunity_hash)\
                .where('status', 'in', ['pending', 'executing'])\
                .limit(1)\
                .get()
            
            if len(existing) > 0:
                self.logger.info(f"Duplicate opportunity detected: {opportunity_hash}")
                return None
            
            # Create opportunity document
            opportunity_doc = {
                'opportunity_hash': opportunity_hash,
                'data': opportunity_data,
                'source_verification': source_verification,
                'status': 'pending',
                'created_at': firestore.SERVER_TIMESTAMP,
                'expires_at': firestore.SERVER_TIMESTAMP,  # Will be set by strategy
                'required_capital': opportunity_data.get('required_capital', 0),
                'estimated_profit': opportunity_data.get('estimated_profit', 0),
                'confidence_score': opportunity_data.get('confidence_score', 0),
                'reserved_by': None,
                'reserved_at': None,
                'executed_at': None,
                'execution_result': None,
                '_metadata': {
                    'version': '1.0',
                    'encryption_level': 'opportunity_hash_only'
                }
            }
            
            doc_ref = self.db.collection(config.COLLECTIONS['opportunities'])\
                .document(opportunity_hash)
            doc_ref.set(opportunity_doc)
            
            self.logger.info(f"Created opportunity signal: {opportunity_hash}")
            return opportunity_hash
            
        except Exception as e:
            self.logger.error(f"Failed to create opportunity signal: {e}")
            return None
    
    def reserve_capital_for_opportunity(self,
                                       agent_id: str,
                                       opportunity_hash: str,
                                       amount: float) -> Tuple[bool, Optional[str]]:
        """
        Reserve capital for an opportunity using distributed reservation system
        Returns (success, reservation_id)
        """
        try:
            reservation_id = f"{opportunity_hash}_{agent_id}"
            
            @firestore.transactional
            def reserve_transaction(transaction, 
                                   opportunity_ref,
                                   capital_pool_ref,
                                   reservation_id,
                                   agent_id,
                                   amount):
                
                # Check opportunity is still available
                opportunity = transaction.get(opportunity_ref)
                if not opportunity.exists:
                    return False, "Opportunity not found"
                
                opp_data = opportunity.to_dict()
                if opp_data['status'] != 'pending':
                    return False, f"Opportunity status is {opp_data['status']}"
                
                # Check capital pool availability
                pool_data = transaction.get(capital_pool_ref).to_dict()
                available = pool_data.get('available_capital', 0)
                
                if available < amount:
                    return False, f"Insufficient capital: {available} < {amount}"
                
                # Update capital pool
                transaction.update(capital_pool_ref, {
                    'available_capital': firestore.Increment(-amount),
                    'reserved_capital': firestore.Increment(amount),
                    f'reservations.{reservation_id}': {
                        'agent_id': agent_id,
                        'amount': amount,
                        'timestamp': firestore.SERVER_TIMESTAMP,
                        'opportunity_hash': opportunity_hash
                    }
                })
                
                # Update opportunity status
                transaction.update(opportunity_ref, {
                    'status': 'reserved',
                    'reserved_by': agent_id,
                    'reserved_at': firestore.SERVER_TIMESTAMP
                })
                
                return True, reservation_id
            
            opportunity_ref = self.db.collection(config.COLLECTIONS['opportunities'])\
                .document(opportunity_hash)
            capital_pool_ref = self.db.collection(config.COLLECTIONS['capital_pools'])\
                .document('main_pool')
            
            return reserve_transaction(
                self.db.transaction(),
                opportunity_ref,
                capital_pool_ref,
                reservation_id,
                agent_id,
                amount
            )
            
        except Exception as e:
            self.logger.error(f"Failed to reserve capital: {e}")
            return False, str(e)
    
    def update_agent_heartbeat(self, agent_id: str, status_data: Dict[str, Any]) -> bool:
        """Update agent heartbeat and status"""
        try:
            agent_ref = self.db.collection(config.COLLECTIONS['agents']).document(agent_id)
            
            update_data = {
                'last_heartbeat': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'current_strategy': status_data.get('current_strategy'),
                'capital_allocated': status_data.get('capital_allocated', 0),
                'performance_24h': status_data.get('performance_24h', 0),
                'current_opportunities': status_data.get('current_opportunities', []),
                '_metadata': {
                    'ip_address': status_data.get('ip_address', 'unknown'),
                    'container_id': status_data.get('container_id', 'unknown'),
                    'version': status_data.get('version', '1.0')
                }
            }
            
            agent_ref.set(update_data, merge=True)
            self.logger.debug(f"Heartbeat updated for agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update agent heartbeat: {e}")
            return False
    
    def get_active_opportunities(self, 
                                min_confidence: float = 0.7,
                                max_age_minutes: int = 5) -> List[Dict[str, Any]]:
        """Retrieve active opportunities meeting criteria"""
        try:
            cutoff_time = datetime.utcnow()
            # In production, we'd use firestore.SERVER_TIMESTAMP comparison
            
            opportunities_ref = self.db.collection(config.COLLECTIONS['opportunities'])
            query = opportunities_ref\
                .where('status', '==', 'pending')\
                .where('confidence_score', '>=', min_confidence)\
                .order_by('confidence_score', direction=firestore.Query.DESCENDING)\
                .limit(20)
            
            docs = query.get()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data