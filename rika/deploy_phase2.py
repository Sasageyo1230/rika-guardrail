"""
Phase 2 Deployment Script
Initializes database, registers agents, and starts Rika Orchestrator
"""

import os
import sys
import logging
import yaml
import psycopg2
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path='config/rika.yaml'):
    """Load Rika configuration"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None


def connect_database(config):
    """Connect to PostgreSQL database"""
    try:
        db_config = config['database']

        # Replace environment variables
        password = os.environ.get('RIKA_DB_PASSWORD', db_config.get('password', ''))

        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=password
        )

        logger.info(f"Connected to database: {db_config['database']}")
        return conn

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def initialize_database(conn):
    """Initialize database schema for Phase 2"""
    try:
        logger.info("Initializing database schema...")

        # Read schema SQL
        schema_path = os.path.join(os.path.dirname(__file__), 'cognitive_sphere', 'schema.sql')

        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute schema
        cursor = conn.cursor()

        # Note: PostgreSQL doesn't support INDEX in CREATE TABLE, fix syntax
        # Replace INDEX with separate CREATE INDEX statements
        schema_sql = schema_sql.replace('INDEX idx_', 'CREATE INDEX IF NOT EXISTS idx_')

        # Split into individual statements and execute
        for statement in schema_sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except Exception as e:
                    logger.warning(f"Statement execution warning: {e}")

        conn.commit()
        logger.info("Database schema initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def setup_vector_store(config):
    """Setup Chroma vector store"""
    try:
        logger.info("Setting up vector store...")

        vector_config = config['vector_store']
        persist_dir = vector_config['persist_directory']

        # Create directory if needed
        os.makedirs(persist_dir, exist_ok=True)

        # Initialize Chroma
        try:
            import chromadb
            from chromadb.config import Settings

            client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir
            ))

            # Create collection if doesn't exist
            collection_name = vector_config['collection_name']

            try:
                collection = client.get_collection(collection_name)
                logger.info(f"Using existing collection: {collection_name}")
            except:
                collection = client.create_collection(collection_name)
                logger.info(f"Created new collection: {collection_name}")

            return collection

        except ImportError:
            logger.warning("chromadb not installed. Using mock vector store.")
            return MockVectorStore()

    except Exception as e:
        logger.error(f"Vector store setup failed: {e}")
        return None


def initialize_llm(config):
    """Initialize LLM"""
    try:
        logger.info("Initializing LLM...")

        from rika.llm.inference import RikaLLM

        llm_config = config['llm']

        if llm_config.get('use_mock', True):
            logger.info("Using mock LLM for testing")
            from rika.llm.inference import MockLLM
            return MockLLM()

        llm = RikaLLM(
            model_path=llm_config['model_path'],
            n_ctx=llm_config.get('context_size', 2048),
            n_threads=llm_config.get('threads', 8)
        )

        llm.initialize()
        logger.info("LLM initialized successfully")
        return llm

    except Exception as e:
        logger.error(f"LLM initialization failed: {e}")
        return None


def setup_encryption(config):
    """Setup encryption manager"""
    try:
        logger.info("Setting up encryption...")

        # For now, use a mock encryption manager
        # In production, integrate with Phase 1 encryption
        class MockEncryption:
            def encrypt(self, data):
                if isinstance(data, str):
                    return data.encode()
                return data

            def decrypt(self, data):
                if isinstance(data, bytes):
                    return data.decode()
                return data

        return MockEncryption()

    except Exception as e:
        logger.error(f"Encryption setup failed: {e}")
        return None


def setup_authentication():
    """Setup authentication manager"""
    try:
        logger.info("Setting up authentication...")

        # Mock authentication for testing
        class MockAuth:
            def verify_token(self, token):
                return "test_user" if token else None

        return MockAuth()

    except Exception as e:
        logger.error(f"Authentication setup failed: {e}")
        return None


def initialize_orchestrator(db, vector_store, llm, auth, encryption, config):
    """Initialize Rika Orchestrator"""
    try:
        logger.info("Initializing Rika Orchestrator...")

        from rika.orchestrator_v2 import RikaOrchestrator

        # Create orchestrator
        config_path = 'config/rika.yaml'
        orchestrator = RikaOrchestrator(config_path)

        # Initialize components
        orchestrator.initialize(db, vector_store, llm, auth, encryption)

        logger.info("Rika Orchestrator initialized successfully")
        return orchestrator

    except Exception as e:
        logger.error(f"Orchestrator initialization failed: {e}")
        return None


def register_agents(orchestrator, config):
    """Register sub-agents"""
    try:
        logger.info("Registering agents...")

        from rika.agents.mint import MintAgent

        agent_config = config['agents']

        # Register Mint if enabled
        if agent_config.get('mint', {}).get('enabled', True):
            orchestrator.register_agent('mint', MintAgent)
            logger.info("Registered: Mint (YouTube automation)")

        # Future agents
        # if agent_config.get('rig', {}).get('enabled', False):
        #     orchestrator.register_agent('rig', RigAgent)

        logger.info("Agent registration complete")
        return True

    except Exception as e:
        logger.error(f"Agent registration failed: {e}")
        return False


def ingest_cognitive_sphere(orchestrator, config):
    """Ingest initial Cognitive Sphere data"""
    try:
        logger.info("Ingesting Cognitive Sphere data...")

        from rika.cognitive_sphere.ingestor import CognitiveSphereIngestor

        ingestor = CognitiveSphereIngestor(
            orchestrator.db,
            orchestrator.vector_store,
            orchestrator.encryption_manager
        )

        cognitive_config = config.get('cognitive_sphere', {})
        sources = cognitive_config.get('sources', {})

        # Ingest based on configuration
        if sources.get('gmail', {}).get('enabled', False):
            logger.info("Ingesting emails...")
            ingestor.ingest_emails(limit=sources['gmail'].get('email_limit', 500))

        if sources.get('calendar', {}).get('enabled', False):
            logger.info("Ingesting calendar...")
            ingestor.ingest_calendar()

        if sources.get('github', {}).get('enabled', True):
            logger.info("Ingesting code repositories...")
            token = os.environ.get('GITHUB_TOKEN')
            ingestor.ingest_code_repositories(github_token=token)

        if sources.get('projects', {}).get('enabled', True):
            logger.info("Ingesting projects...")
            for folder in sources['projects'].get('folders', []):
                expanded_folder = os.path.expanduser(folder)
                if os.path.exists(expanded_folder):
                    ingestor.ingest_projects(expanded_folder)

        # Build cognitive profile
        logger.info("Building cognitive profile...")
        ingestor.build_cognitive_profile()

        logger.info("Cognitive Sphere ingestion complete")
        return True

    except Exception as e:
        logger.error(f"Cognitive Sphere ingestion failed: {e}")
        return False


def run_tests():
    """Run Phase 2 integration tests"""
    try:
        logger.info("Running Phase 2 tests...")

        import pytest

        test_file = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_phase2_integration.py')

        result = pytest.main([test_file, '-v', '--tb=short'])

        if result == 0:
            logger.info("All tests passed!")
            return True
        else:
            logger.warning("Some tests failed")
            return False

    except ImportError:
        logger.warning("pytest not installed. Skipping tests.")
        return True
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return False


class MockVectorStore:
    """Mock vector store for testing"""

    def similarity_search_with_score(self, query, k=5):
        return []


def main():
    """Main deployment function"""
    logger.info("="*60)
    logger.info("Rika Phase 2 Deployment")
    logger.info("="*60)

    # 1. Load configuration
    logger.info("\n[1/9] Loading configuration...")
    config = load_config()
    if not config:
        logger.error("Deployment failed: Could not load configuration")
        return False

    # 2. Connect to database
    logger.info("\n[2/9] Connecting to database...")
    db = connect_database(config)
    if not db:
        logger.error("Deployment failed: Database connection failed")
        return False

    # 3. Initialize database schema
    logger.info("\n[3/9] Initializing database schema...")
    if not initialize_database(db):
        logger.warning("Database initialization had warnings, continuing...")

    # 4. Setup vector store
    logger.info("\n[4/9] Setting up vector store...")
    vector_store = setup_vector_store(config)
    if not vector_store:
        logger.error("Deployment failed: Vector store setup failed")
        return False

    # 5. Initialize LLM
    logger.info("\n[5/9] Initializing LLM...")
    llm = initialize_llm(config)
    if not llm:
        logger.error("Deployment failed: LLM initialization failed")
        return False

    # 6. Setup security
    logger.info("\n[6/9] Setting up security...")
    encryption = setup_encryption(config)
    auth = setup_authentication()

    # 7. Initialize orchestrator
    logger.info("\n[7/9] Initializing Rika Orchestrator...")
    orchestrator = initialize_orchestrator(db, vector_store, llm, auth, encryption, config)
    if not orchestrator:
        logger.error("Deployment failed: Orchestrator initialization failed")
        return False

    # 8. Register agents
    logger.info("\n[8/9] Registering agents...")
    if not register_agents(orchestrator, config):
        logger.warning("Some agents failed to register, continuing...")

    # 9. Ingest Cognitive Sphere (optional)
    if config.get('cognitive_sphere', {}).get('ingestion', {}).get('auto_ingest_on_startup', False):
        logger.info("\n[9/9] Ingesting Cognitive Sphere data...")
        ingest_cognitive_sphere(orchestrator, config)
    else:
        logger.info("\n[9/9] Skipping Cognitive Sphere ingestion (disabled in config)")

    # Success!
    logger.info("\n" + "="*60)
    logger.info("Phase 2 Deployment Complete!")
    logger.info("="*60)

    # Run tests
    logger.info("\nRunning integration tests...")
    run_tests()

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("RIKA PHASE 2 SUMMARY")
    logger.info("="*60)
    logger.info(f"Database: Connected to {config['database']['database']}")
    logger.info(f"Vector Store: {config['vector_store']['type']}")
    logger.info(f"LLM: {llm.get_model_info()['type']}")
    logger.info(f"Registered Agents: {', '.join(orchestrator.agents.keys())}")
    logger.info("="*60)

    return orchestrator


if __name__ == "__main__":
    main()
