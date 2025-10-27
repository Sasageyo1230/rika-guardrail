"""
Simple script to run Rika Phase 2
"""

import logging
from deploy_phase2 import main as deploy_main

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def interactive_mode(orchestrator):
    """Run Rika in interactive mode"""
    logger.info("\n" + "="*60)
    logger.info("Rika Interactive Mode")
    logger.info("Type 'exit' or 'quit' to exit")
    logger.info("="*60 + "\n")

    session_token = "interactive_session"

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', 'q']:
                logger.info("Goodbye!")
                break

            # Process request
            response = orchestrator.process_request(user_input, session_token)

            # Display response
            if response["status"] == "SUCCESS":
                print(f"\nRika: {response['response']}")

                if response.get('confidence'):
                    print(f"(Confidence: {response['confidence']:.0%})")

                if response.get('actions_taken'):
                    print(f"\nActions: {response['actions_taken']}")

            elif response["status"] == "PENDING_APPROVAL":
                print(f"\nRika: {response.get('response', 'Action requires your approval.')}")
                print(f"Approval ID: {response.get('actions_taken', {}).get('approval_id', 'N/A')}")

            else:
                print(f"\nRika: {response.get('response', 'Error processing request.')}")
                if response.get('reason'):
                    print(f"Reason: {response['reason']}")

        except KeyboardInterrupt:
            logger.info("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")


def test_mode(orchestrator):
    """Run Rika with test queries"""
    logger.info("\n" + "="*60)
    logger.info("Rika Test Mode")
    logger.info("="*60 + "\n")

    test_queries = [
        "What's on my calendar?",
        "How are my YouTube videos performing?",
        "What projects am I working on?",
        "What's my typical working schedule?",
        "Can you analyze my recent video performance?"
    ]

    session_token = "test_session"

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n[Test {i}/{len(test_queries)}] User: {query}")

        response = orchestrator.process_request(query, session_token)

        if response["status"] == "SUCCESS":
            logger.info(f"Rika: {response['response'][:200]}...")
        else:
            logger.info(f"Status: {response['status']}")

    logger.info("\nTest mode complete")


if __name__ == "__main__":
    import sys

    # Deploy Rika
    logger.info("Starting Rika deployment...")
    orchestrator = deploy_main()

    if not orchestrator:
        logger.error("Deployment failed. Exiting.")
        sys.exit(1)

    # Check mode
    mode = sys.argv[1] if len(sys.argv) > 1 else "interactive"

    if mode == "test":
        test_mode(orchestrator)
    elif mode == "interactive":
        interactive_mode(orchestrator)
    else:
        logger.info(f"Unknown mode: {mode}")
        logger.info("Usage: python run_rika.py [interactive|test]")
