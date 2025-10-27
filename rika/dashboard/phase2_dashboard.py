"""
Phase 2 Dashboard
Shows progress, agent status, and system health
"""

import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class Phase2Dashboard:
    """Dashboard for Phase 2 monitoring"""

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)

    def get_system_status(self) -> Dict:
        """Get overall system status"""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "phase": "Phase 2 - Orchestrator + Mint MVP",
                "status": "operational",
                "components": {}
            }

            if self.orchestrator:
                # Check database
                status["components"]["database"] = self._check_database()

                # Check vector store
                status["components"]["vector_store"] = self._check_vector_store()

                # Check LLM
                status["components"]["llm"] = self._check_llm()

                # Check agents
                status["components"]["agents"] = self._check_agents()

            return status

        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {"status": "error", "error": str(e)}

    def get_agent_status(self) -> List[Dict]:
        """Get status of all registered agents"""
        agents_status = []

        if self.orchestrator:
            for agent_name, agent in self.orchestrator.agents.items():
                agents_status.append({
                    "name": agent_name,
                    "type": agent.__class__.__name__,
                    "status": "active",
                    "registered_at": "unknown"
                })

        return agents_status

    def get_cognitive_sphere_stats(self) -> Dict:
        """Get Cognitive Sphere statistics"""
        try:
            if not self.orchestrator or not self.orchestrator.db:
                return {"error": "Database not available"}

            cursor = self.orchestrator.db.cursor()

            # Count cognitive data entries
            cursor.execute("SELECT COUNT(*) FROM cognitive_data")
            data_count = cursor.fetchone()[0] if cursor.rowcount > 0 else 0

            # Count by type
            cursor.execute("""
                SELECT data_type, COUNT(*) as count
                FROM cognitive_data
                GROUP BY data_type
            """)
            type_counts = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total_entries": data_count,
                "by_type": type_counts,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting cognitive sphere stats: {e}")
            return {"error": str(e)}

    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversations"""
        try:
            if not self.orchestrator or not self.orchestrator.db:
                return []

            cursor = self.orchestrator.db.cursor()

            cursor.execute("""
                SELECT user_input, rika_response, timestamp
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))

            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    "user_input": row[0],
                    "response": row[1].get("text", "") if isinstance(row[1], dict) else "",
                    "timestamp": row[2].isoformat() if row[2] else None
                })

            return conversations

        except Exception as e:
            self.logger.error(f"Error getting conversations: {e}")
            return []

    def get_mint_analytics(self) -> Dict:
        """Get Mint agent analytics"""
        try:
            if not self.orchestrator or not self.orchestrator.db:
                return {"error": "Database not available"}

            cursor = self.orchestrator.db.cursor()

            # Get video count
            cursor.execute("SELECT COUNT(*) FROM mint_videos")
            video_count = cursor.fetchone()[0] if cursor.rowcount > 0 else 0

            # Get total views/revenue (if available)
            cursor.execute("""
                SELECT SUM(value) FROM mint_analytics WHERE metric_type = 'views'
            """)
            total_views = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT SUM(value) FROM mint_analytics WHERE metric_type = 'revenue'
            """)
            total_revenue = cursor.fetchone()[0] or 0

            return {
                "total_videos": video_count,
                "total_views": int(total_views),
                "total_revenue": float(total_revenue),
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting Mint analytics: {e}")
            return {"error": str(e)}

    def render_text_dashboard(self) -> str:
        """Render text-based dashboard"""
        output = []

        output.append("=" * 70)
        output.append("RIKA PHASE 2 DASHBOARD")
        output.append("=" * 70)
        output.append("")

        # System status
        status = self.get_system_status()
        output.append(f"Status: {status.get('status', 'unknown').upper()}")
        output.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")

        # Components
        output.append("COMPONENTS:")
        output.append("-" * 70)
        for component, state in status.get("components", {}).items():
            output.append(f"  {component:20s} {state}")
        output.append("")

        # Agents
        output.append("REGISTERED AGENTS:")
        output.append("-" * 70)
        agents = self.get_agent_status()
        for agent in agents:
            output.append(f"  {agent['name']:20s} {agent['type']:30s} [{agent['status']}]")
        if not agents:
            output.append("  No agents registered")
        output.append("")

        # Cognitive Sphere
        output.append("COGNITIVE SPHERE:")
        output.append("-" * 70)
        cs_stats = self.get_cognitive_sphere_stats()
        if "error" not in cs_stats:
            output.append(f"  Total entries: {cs_stats.get('total_entries', 0)}")
            for data_type, count in cs_stats.get('by_type', {}).items():
                output.append(f"    {data_type:30s} {count}")
        else:
            output.append(f"  Error: {cs_stats['error']}")
        output.append("")

        # Mint Analytics
        output.append("MINT AGENT (YouTube):")
        output.append("-" * 70)
        mint_stats = self.get_mint_analytics()
        if "error" not in mint_stats:
            output.append(f"  Videos: {mint_stats.get('total_videos', 0)}")
            output.append(f"  Total Views: {mint_stats.get('total_views', 0):,}")
            output.append(f"  Total Revenue: ${mint_stats.get('total_revenue', 0):.2f}")
        else:
            output.append(f"  Error: {mint_stats['error']}")
        output.append("")

        # Recent activity
        output.append("RECENT CONVERSATIONS:")
        output.append("-" * 70)
        conversations = self.get_recent_conversations(limit=5)
        for conv in conversations:
            output.append(f"  {conv['timestamp']}: {conv['user_input'][:50]}...")
        if not conversations:
            output.append("  No conversations yet")
        output.append("")

        output.append("=" * 70)

        return "\n".join(output)

    def _check_database(self) -> str:
        """Check database connection"""
        try:
            if self.orchestrator.db:
                cursor = self.orchestrator.db.cursor()
                cursor.execute("SELECT 1")
                return "✓ Connected"
            return "✗ Not connected"
        except Exception as e:
            return f"✗ Error: {str(e)[:30]}"

    def _check_vector_store(self) -> str:
        """Check vector store"""
        try:
            if self.orchestrator.vector_store:
                return "✓ Available"
            return "✗ Not available"
        except Exception as e:
            return f"✗ Error: {str(e)[:30]}"

    def _check_llm(self) -> str:
        """Check LLM"""
        try:
            if self.orchestrator.llm:
                model_info = self.orchestrator.llm.get_model_info()
                return f"✓ {model_info['type']}"
            return "✗ Not loaded"
        except Exception as e:
            return f"✗ Error: {str(e)[:30]}"

    def _check_agents(self) -> str:
        """Check agents"""
        try:
            count = len(self.orchestrator.agents)
            return f"✓ {count} registered"
        except Exception as e:
            return f"✗ Error: {str(e)[:30]}"


def main():
    """Run dashboard standalone"""
    import sys
    sys.path.insert(0, '..')

    from deploy_phase2 import main as deploy_main

    # Deploy Rika
    orchestrator = deploy_main()

    if orchestrator:
        # Create dashboard
        dashboard = Phase2Dashboard(orchestrator)

        # Render
        print(dashboard.render_text_dashboard())


if __name__ == "__main__":
    main()
