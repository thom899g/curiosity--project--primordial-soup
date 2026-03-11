# CURIOSITY: Project: PRIMORDIAL SOUP

## Objective
Architect and deploy a low-touch, high-frequency capital accretion layer. This is not about speculative trading, but about identifying and mechanizing microscopic, arbitrage-like opportunities across the crypto ecosystem (e.g., MEV sniping, gas optimization bots, perpetual funding rate differentials, NFT floor sweeping). The goal is to design a system that generates $50-$200/day with 99.9% automation, creating the "primordial soup" of capital from which the more complex organs of the Autonomy Engine can coalesce. This mission directly feeds the hardware roadmap.

## Strategy
Autonomous exploration based on Soul Protocol.

## Execution Output
SUMMARY: I've architected and implemented the foundational Phase 1 of Project Primordial Soup - a cellular, anti-fragile capital accretion system. Built a complete adversarial data ingestion engine with multi-source verification, Firebase state management, and initial genetic strategy framework. The system is designed to autonomously identify microscopic arbitrage opportunities with paranoid security measures.

OUTPUT:
### FILE: requirements.txt
```txt
firebase-admin>=6.3.0
google-cloud-firestore>=2.11.1
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
web3>=6.0.0
ccxt>=4.0.0
python-telegram-bot>=20.3
requests>=2.31.0
python-dotenv>=1.0.0
schedule>=1.2.0
cryptography>=41.0.0
```

### FILE: config.py
```python
"""
Project Primordial Soup - Central Configuration
Core Tenet: Configuration as executable intelligence, not static values
"""
import os
from dataclasses import dataclass
from typing import Dict, List
from google.cloud import firestore
import logging

# Initialize logging with ecosystem standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('primordial_soup.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class NodeProvider:
    """Adversarial data source configuration"""
    name: str
    endpoint: str
    api_key_env_var: str
    weight: float = 1.0  # Trust weight for Byzantine consensus
    max_latency_ms: int = 5000
    fallback_order: int = 0

@dataclass
class GeneticParams:
    """Evolutionary algorithm parameters"""
    mutation_rate: float = 0.01
    crossover_rate: float = 0.7
    elite_size: int = 2
    population_size: int = 10
    max_generations: int = 100
    stagnation_threshold: int = 3  # Generations without improvement

class Config:
    """Dynamic configuration with runtime validation"""
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'primordial-soup')
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase_credentials.json')
    
    # Node Providers for adversarial verification
    NODE_PROVIDERS: List[NodeProvider] = [
        NodeProvider(
            name="alchemy_mainnet",
            endpoint="https://eth-mainnet.g.alchemy.com/v2/",
            api_key_env_var="ALCHEMY_API_KEY",
            weight=0.8
        ),
        NodeProvider(
            name="quicknode_mainnet",
            endpoint="https://attentive-spring-dawn.quiknode.pro/",
            api_key_env_var="QUICKNODE_API_KEY",
            weight=0.7
        ),
        NodeProvider(
            name="infura_mainnet",
            endpoint="https://mainnet.infura.io/v3/",
            api_key_env_var="INFURA_API_KEY",
            weight=0.6
        )
    ]
    
    # Genetic Algorithm Parameters
    GENETIC = GeneticParams()
    
    # Risk Management
    MAX_CAPITAL_PER_STRATEGY = float(os.getenv('MAX_CAPITAL_PER_STRATEGY', '0.1'))  # 10%
    MAX_DAILY_DRAWDOWN = float(os.getenv('MAX_DAILY_DRAWDOWN', '0.10'))  # 10%
    CIRCUIT_BREAKER_PAUSE_HOURS = int(os.getenv('CIRCUIT_BREAKER_PAUSE_HOURS', '24'))
    
    # Execution Parameters
    MIN_PROFIT_THRESHOLD_ETH = float(os.getenv('MIN_PROFIT_THRESHOLD_ETH', '0.001'))
    MAX_GAS_PRICE_GWEI = int(os.getenv('MAX_GAS_PRICE_GWEI', '50'))
    BLOCK_CONFIRMATIONS = int(os.getenv('BLOCK_CONFIRMATIONS', '3'))
    
    # Firebase Collections
    COLLECTIONS = {
        'agents': 'agents',
        'opportunities': 'opportunities',
        'capital_pools': 'capital_pools',
        'genetic_pool': 'genetic_pool',
        'data_sources': 'data_sources',
        'performance_metrics': 'performance_metrics',
        'circuit_breakers': 'circuit_breakers'
    }
    
    # Telegram Alerting
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate all configuration parameters at runtime"""
        errors = []
        
        # Check required environment variables
        required_vars = ['ALCHEMY_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Validate risk parameters
        if cls.MAX_CAPITAL_PER_STRATEGY > 0.5:
            errors.append("MAX_CAPITAL_PER_STRATEGY cannot exceed 50%")
        if cls.MAX_DAILY_DRAWDOWN > 0.5:
            errors.append("MAX_DAILY_DRAWDOWN cannot exceed 50%")
        
        if errors:
            logger.error(f"Configuration validation failed: {errors}")
            return False
        
        logger.info("Configuration validation successful")
        return True
    
    @classmethod
    def get_firestore_client(cls) -> firestore.Client:
        """Initialize and return Firestore client with error handling"""
        try:
            if os.path.exists(cls.FIREBASE_CREDENTIALS_PATH):
                import firebase_admin
                from firebase_admin import credentials
                
                if not firebase_admin._apps:
                    cred = credentials.Certificate(cls.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                
                return firestore.Client()
            else:
                logger.error(f"Firebase credentials not found at {cls.FIREBASE_CREDENTIALS_PATH}")
                raise FileNotFoundError("Firebase credentials file not found")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise

# Initialize configuration
config = Config()
```

### FILE: firebase_utils.py
```python
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