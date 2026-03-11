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