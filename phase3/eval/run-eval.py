# phase3/eval/run-eval.py
# CLI Runner for Rika Evaluation Harness

import asyncio
import argparse
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import structlog
from evaluator import EvaluationRunner

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

def load_config():
    """Load configuration from environment and .env file"""
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        "db_url": os.getenv("DATABASE_URL", "postgresql://rika_admin:RikaPostgres2025SecureDB@localhost:5433/rika_core"),
        "core_api_url": os.getenv("CORE_API_URL", "http://localhost:5317"),
        "minio_config": {
            "url": os.getenv("MINIO_URL", "http://localhost:9000"),
            "access_key": os.getenv("MINIO_ACCESS_KEY", "rika_minio_admin"),
            "secret_key": os.getenv("MINIO_SECRET_KEY", "MinioStorage2025RikaS3Obj")
        },
        "gold_tasks_dir": os.getenv("EVAL_GOLD_TASKS_PATH", "gold_tasks"),
        "max_workers": int(os.getenv("EVAL_MAX_WORKERS", "4")),
        "timeout_seconds": int(os.getenv("EVAL_TIMEOUT_SECONDS", "30"))
    }

async def run_evaluation(domains=None, suites=None, output_file=None, verbose=False):
    """Run evaluation suites"""
    config = load_config()
    runner = EvaluationRunner(
        config["db_url"],
        config["minio_config"], 
        config["core_api_url"]
    )
    
    # Generate run ID
    run_id = f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting evaluation run: {run_id}")
    
    # Load gold tasks
    logger.info(f"Loading gold tasks from: {config['gold_tasks_dir']}")
    all_suites = await runner.load_gold_tasks(config["gold_tasks_dir"])
    
    if not all_suites:
        logger.error("No evaluation suites found!")
        return False
    
    # Filter suites
    suites_to_run = {}
    if domains:
        for domain in domains:
            if domain in all_suites:
                suites_to_run[domain] = all_suites[domain]
            else:
                logger.warning(f"Domain not found: {domain}")
    elif suites:
        for suite_name in suites:
            if suite_name in all_suites:
                suites_to_run[suite_name] = all_suites[suite_name]
            else:
                logger.warning(f"Suite not found: {suite_name}")
    else:
        suites_to_run = all_suites
    
    if not suites_to_run:
        logger.error("No suites to run after filtering!")
        return False
    
    logger.info(f"Running {len(suites_to_run)} suite(s): {list(suites_to_run.keys())}")
    
    # Run evaluations
    all_results = []
    suite_summaries = {}
    
    for suite_name, suite in suites_to_run.items():
        logger.info(f"Running suite: {suite_name}")
        
        try:
            results = await runner.run_suite(suite, config["max_workers"])
            
            # Save results
            await runner.save_results(run_id, suite_name, results)
            
            # Calculate summary
            summary = runner.calculate_suite_summary(results)
            suite_summaries[suite_name] = summary
            
            all_results.extend(results)
            
            if verbose:
                logger.info(f"Suite {suite_name} completed:")
                logger.info(f"  Tasks: {summary['total_tasks']}")
                logger.info(f"  Success rate: {summary['success_rate']:.2%}")
                logger.info(f"  Avg latency: {summary['avg_latency_ms']:.1f}ms")
                logger.info(f"  P95 latency: {summary['p95_latency_ms']:.1f}ms")
                
        except Exception as e:
            logger.error(f"Suite {suite_name} failed: {e}")
            continue
    
    # Generate overall summary
    overall_summary = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "domains_requested": domains,
            "suites_requested": suites,
            "max_workers": config["max_workers"]
        },
        "suite_summaries": suite_summaries,
        "overall_stats": runner.calculate_suite_summary(all_results) if all_results else {}
    }
    
    # Save summary
    summary_json = json.dumps(overall_summary, indent=2, default=str)
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary_json)
        logger.info(f"Results saved to: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print(f"EVALUATION SUMMARY - Run ID: {run_id}")
    print("="*60)
    
    if overall_summary["overall_stats"]:
        stats = overall_summary["overall_stats"]
        print(f"Total Tasks: {stats['total_tasks']}")
        print(f"Success Rate: {stats['success_rate']:.2%}")
        print(f"Failed Tasks: {stats['failed_tasks']}")
        print(f"Average Latency: {stats['avg_latency_ms']:.1f}ms")
        print(f"P95 Latency: {stats['p95_latency_ms']:.1f}ms")
        
        print("\nDomain Breakdown:")
        for domain, domain_stats in stats.get("domain_summaries", {}).items():
            print(f"  {domain}:")
            print(f"    Tasks: {domain_stats['task_count']}")
            print(f"    Success Rate: {domain_stats['success_rate']:.2%}")
            if domain_stats.get("avg_metrics"):
                print(f"    Key Metrics:")
                for metric, value in domain_stats["avg_metrics"].items():
                    if isinstance(value, (int, float)):
                        print(f"      {metric}: {value:.3f}")
    
    print(f"\nDetailed results stored in database and MinIO with run ID: {run_id}")
    print("="*60)
    
    return len(all_results) > 0 and overall_summary["overall_stats"].get("success_rate", 0) > 0.5

async def list_available_suites():
    """List available evaluation suites"""
    config = load_config()
    runner = EvaluationRunner(
        config["db_url"],
        config["minio_config"],
        config["core_api_url"]
    )
    
    suites = await runner.load_gold_tasks(config["gold_tasks_dir"])
    
    print("Available Evaluation Suites:")
    print("="*40)
    
    for domain, suite in suites.items():
        print(f"\nDomain: {domain}")
        print(f"  Suite: {suite.name}")
        print(f"  Description: {suite.description}")
        print(f"  Tasks: {len(suite.tasks)}")
        print(f"  Version: {suite.metadata.get('version', 'N/A')}")
        
        # Show task breakdown
        task_categories = {}
        for task in suite.tasks:
            category = task.metadata.get('category', 'unknown')
            task_categories[category] = task_categories.get(category, 0) + 1
        
        if task_categories:
            print(f"  Categories: {', '.join(f'{cat}({count})' for cat, count in task_categories.items())}")

def main():
    parser = argparse.ArgumentParser(description="Rika Evaluation Harness")
    parser.add_argument("--domains", nargs="+", help="Specific domains to evaluate (presence_query, link_command, retrieval_qa)")
    parser.add_argument("--suites", nargs="+", help="Specific suite names to run")
    parser.add_argument("--output", "-o", help="Output file for results summary")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--list", "-l", action="store_true", help="List available suites and exit")
    
    args = parser.parse_args()
    
    if args.list:
        asyncio.run(list_available_suites())
        return
    
    try:
        success = asyncio.run(run_evaluation(
            domains=args.domains,
            suites=args.suites, 
            output_file=args.output,
            verbose=args.verbose
        ))
        
        if not success:
            print("Evaluation completed with issues. Check logs for details.")
            exit(1)
        else:
            print("Evaluation completed successfully!")
            
    except KeyboardInterrupt:
        print("\nEvaluation interrupted by user.")
        exit(1)
    except Exception as e:
        print(f"Evaluation failed with error: {e}")
        logger.error(f"Evaluation error: {e}")
        exit(1)

if __name__ == "__main__":
    main()