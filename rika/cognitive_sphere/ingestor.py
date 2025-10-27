"""
Cognitive Sphere Data Ingestion System
Ingests data about user's life, patterns, knowledge, and context
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib

logger = logging.getLogger(__name__)


class CognitiveSphereIngestor:
    """Ingest data into Cognitive Sphere (your thoughts, patterns, knowledge)"""

    def __init__(self, db_connection, vector_store, encryption_manager):
        """
        Initialize the Cognitive Sphere Ingestor

        Args:
            db_connection: Database connection for storing structured data
            vector_store: Vector database for embeddings and semantic search
            encryption_manager: Encryption manager from Phase 1 security
        """
        self.db = db_connection
        self.vector_store = vector_store
        self.encryption = encryption_manager
        self.logger = logging.getLogger(__name__)

    def ingest_emails(self, gmail_connection=None, limit: int = 500) -> Dict[str, Any]:
        """
        Fetch emails (1-2 months back), parse for:
        - Sender relationships
        - Topics (what you discuss, care about)
        - Communication patterns (response time, tone, keywords)
        - Work context

        Store in Cognitive Sphere with embeddings.

        Args:
            gmail_connection: Gmail API connection (if None, uses mock data for testing)
            limit: Maximum number of emails to ingest

        Returns:
            Dict with ingestion statistics
        """
        self.logger.info(f"Starting email ingestion (limit: {limit})")

        stats = {
            "emails_processed": 0,
            "relationships_identified": 0,
            "topics_extracted": 0,
            "errors": 0
        }

        try:
            # Fetch emails from the last 2 months
            emails = self._fetch_emails(gmail_connection, limit)

            for email in emails:
                try:
                    # Extract relationship data
                    relationship = self._analyze_email_relationship(email)
                    if relationship:
                        self._store_cognitive_data(
                            data_type="email_relationship",
                            source="gmail",
                            content=relationship,
                            timestamp=email.get("date")
                        )
                        stats["relationships_identified"] += 1

                    # Extract topics
                    topics = self._extract_topics(email)
                    for topic in topics:
                        self._store_cognitive_data(
                            data_type="communication_topic",
                            source="gmail",
                            content=topic,
                            timestamp=email.get("date")
                        )
                        stats["topics_extracted"] += 1

                    # Extract communication patterns
                    pattern = self._analyze_communication_pattern(email)
                    if pattern:
                        self._store_cognitive_data(
                            data_type="communication_pattern",
                            source="gmail",
                            content=pattern,
                            timestamp=email.get("date")
                        )

                    stats["emails_processed"] += 1

                except Exception as e:
                    self.logger.error(f"Error processing email: {e}")
                    stats["errors"] += 1

            self.logger.info(f"Email ingestion complete: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Email ingestion failed: {e}")
            raise

    def ingest_calendar(self, calendar_connection=None) -> Dict[str, Any]:
        """
        Fetch calendar events, extract:
        - Schedule patterns (when you focus, meetings, free time)
        - Energy levels (busy days vs. light days)
        - Location patterns
        - Time commitments by category

        Build model of your typical week/month.

        Args:
            calendar_connection: Calendar API connection (if None, uses mock data)

        Returns:
            Dict with ingestion statistics
        """
        self.logger.info("Starting calendar ingestion")

        stats = {
            "events_processed": 0,
            "patterns_identified": 0,
            "errors": 0
        }

        try:
            # Fetch calendar events from the last 3 months
            events = self._fetch_calendar_events(calendar_connection, months=3)

            # Analyze schedule patterns
            schedule_patterns = self._analyze_schedule_patterns(events)
            for pattern in schedule_patterns:
                self._store_cognitive_data(
                    data_type="schedule_pattern",
                    source="calendar",
                    content=pattern,
                    timestamp=datetime.now()
                )
                stats["patterns_identified"] += 1

            # Analyze energy levels by day/time
            energy_patterns = self._analyze_energy_patterns(events)
            for pattern in energy_patterns:
                self._store_cognitive_data(
                    data_type="energy_pattern",
                    source="calendar",
                    content=pattern,
                    timestamp=datetime.now()
                )

            # Store individual events for context
            for event in events:
                self._store_cognitive_data(
                    data_type="calendar_event",
                    source="calendar",
                    content=event,
                    timestamp=event.get("start_time")
                )
                stats["events_processed"] += 1

            self.logger.info(f"Calendar ingestion complete: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Calendar ingestion failed: {e}")
            raise

    def ingest_code_repositories(self, github_token: str = None) -> Dict[str, Any]:
        """
        Scan local + GitHub repos, extract:
        - Coding style, preferences
        - Languages you use
        - Project patterns (what you build, why)
        - Collaboration patterns
        - Technical interests

        Args:
            github_token: GitHub API token (optional, for remote repos)

        Returns:
            Dict with ingestion statistics
        """
        self.logger.info("Starting code repository ingestion")

        stats = {
            "repos_analyzed": 0,
            "patterns_identified": 0,
            "errors": 0
        }

        try:
            # Scan local repositories
            local_repos = self._scan_local_repositories()

            for repo in local_repos:
                try:
                    # Analyze coding style
                    coding_style = self._analyze_coding_style(repo)
                    self._store_cognitive_data(
                        data_type="coding_style",
                        source="github",
                        content=coding_style,
                        timestamp=datetime.now()
                    )

                    # Extract project patterns
                    project_pattern = self._analyze_project_pattern(repo)
                    self._store_cognitive_data(
                        data_type="project_pattern",
                        source="github",
                        content=project_pattern,
                        timestamp=datetime.now()
                    )

                    stats["repos_analyzed"] += 1
                    stats["patterns_identified"] += 2

                except Exception as e:
                    self.logger.error(f"Error analyzing repo {repo.get('name')}: {e}")
                    stats["errors"] += 1

            self.logger.info(f"Code repository ingestion complete: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Code repository ingestion failed: {e}")
            raise

    def ingest_projects(self, projects_folder: str) -> Dict[str, Any]:
        """
        Scan your projects folder, understand:
        - What you're working on
        - Project status (active, paused, complete)
        - Dependencies between projects
        - Creative direction

        Args:
            projects_folder: Path to projects directory

        Returns:
            Dict with ingestion statistics
        """
        self.logger.info(f"Starting project ingestion from: {projects_folder}")

        stats = {
            "projects_analyzed": 0,
            "patterns_identified": 0,
            "errors": 0
        }

        try:
            if not os.path.exists(projects_folder):
                self.logger.warning(f"Projects folder not found: {projects_folder}")
                return stats

            # Scan project directories
            projects = self._scan_project_directories(projects_folder)

            for project in projects:
                try:
                    # Analyze project status
                    project_info = self._analyze_project_status(project)
                    self._store_cognitive_data(
                        data_type="project_info",
                        source="projects",
                        content=project_info,
                        timestamp=datetime.now()
                    )

                    stats["projects_analyzed"] += 1

                except Exception as e:
                    self.logger.error(f"Error analyzing project {project}: {e}")
                    stats["errors"] += 1

            # Analyze dependencies between projects
            dependencies = self._analyze_project_dependencies(projects)
            if dependencies:
                self._store_cognitive_data(
                    data_type="project_dependencies",
                    source="projects",
                    content=dependencies,
                    timestamp=datetime.now()
                )
                stats["patterns_identified"] += 1

            self.logger.info(f"Project ingestion complete: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Project ingestion failed: {e}")
            raise

    def ingest_conversation_history(self, conversation_db) -> Dict[str, Any]:
        """
        Load past Rika conversations, extract:
        - Patterns in how you think
        - Decisions you've made
        - Feedback you've given (how Rika should improve)
        - Topics you care about

        Args:
            conversation_db: Database connection for conversations

        Returns:
            Dict with ingestion statistics
        """
        self.logger.info("Starting conversation history ingestion")

        stats = {
            "conversations_processed": 0,
            "patterns_identified": 0,
            "errors": 0
        }

        try:
            # Fetch past conversations
            conversations = self._fetch_conversations(conversation_db)

            for conversation in conversations:
                try:
                    # Extract thinking patterns
                    thinking_pattern = self._analyze_thinking_pattern(conversation)
                    if thinking_pattern:
                        self._store_cognitive_data(
                            data_type="thinking_pattern",
                            source="conversations",
                            content=thinking_pattern,
                            timestamp=conversation.get("timestamp")
                        )
                        stats["patterns_identified"] += 1

                    # Extract feedback
                    feedback = self._extract_feedback(conversation)
                    if feedback:
                        self._store_cognitive_data(
                            data_type="user_feedback",
                            source="conversations",
                            content=feedback,
                            timestamp=conversation.get("timestamp")
                        )

                    stats["conversations_processed"] += 1

                except Exception as e:
                    self.logger.error(f"Error processing conversation: {e}")
                    stats["errors"] += 1

            self.logger.info(f"Conversation history ingestion complete: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Conversation history ingestion failed: {e}")
            raise

    def build_cognitive_profile(self) -> Dict[str, Any]:
        """
        Synthesize all ingested data into a profile:
        - Your working style
        - Communication style
        - Values (inferred from projects, emails, decisions)
        - Patterns and habits
        - Known preferences

        Used by Rika to personalize responses + future agent behavior.

        Returns:
            Cognitive profile dict
        """
        self.logger.info("Building cognitive profile")

        try:
            # Retrieve all cognitive data
            all_data = self._retrieve_all_cognitive_data()

            profile = {
                "working_style": self._synthesize_working_style(all_data),
                "communication_style": self._synthesize_communication_style(all_data),
                "values": self._infer_values(all_data),
                "patterns": self._identify_patterns(all_data),
                "preferences": self._extract_preferences(all_data),
                "generated_at": datetime.now().isoformat()
            }

            # Store profile in database
            self._store_cognitive_profile(profile)

            self.logger.info("Cognitive profile built successfully")
            return profile

        except Exception as e:
            self.logger.error(f"Failed to build cognitive profile: {e}")
            raise

    # Private helper methods

    def _fetch_emails(self, gmail_connection, limit: int) -> List[Dict]:
        """Fetch emails from Gmail API or return mock data"""
        if gmail_connection is None:
            # Return mock data for testing
            return [
                {
                    "id": f"email_{i}",
                    "from": f"sender{i}@example.com",
                    "subject": f"Test Email {i}",
                    "body": f"This is test email body {i}",
                    "date": datetime.now() - timedelta(days=i)
                }
                for i in range(min(limit, 10))
            ]

        # TODO: Implement actual Gmail API integration
        return []

    def _analyze_email_relationship(self, email: Dict) -> Optional[Dict]:
        """Analyze sender relationship from email"""
        return {
            "sender": email.get("from"),
            "frequency": "regular",
            "context": "work" if "work" in email.get("subject", "").lower() else "personal",
            "last_contact": email.get("date")
        }

    def _extract_topics(self, email: Dict) -> List[Dict]:
        """Extract topics from email content"""
        # Simple keyword extraction (can be enhanced with NLP)
        subject = email.get("subject", "").lower()
        topics = []

        topic_keywords = {
            "work": ["project", "meeting", "deadline", "task"],
            "creative": ["design", "art", "creative", "idea"],
            "technical": ["code", "bug", "deployment", "api"],
            "personal": ["family", "friend", "weekend", "vacation"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in subject for keyword in keywords):
                topics.append({
                    "topic": topic,
                    "keywords": [kw for kw in keywords if kw in subject],
                    "confidence": 0.7
                })

        return topics

    def _analyze_communication_pattern(self, email: Dict) -> Optional[Dict]:
        """Analyze communication patterns from email"""
        return {
            "response_time": "quick" if "Re:" in email.get("subject", "") else "normal",
            "tone": "professional",
            "length": len(email.get("body", ""))
        }

    def _fetch_calendar_events(self, calendar_connection, months: int) -> List[Dict]:
        """Fetch calendar events"""
        if calendar_connection is None:
            # Return mock data
            return [
                {
                    "id": f"event_{i}",
                    "title": f"Meeting {i}",
                    "start_time": datetime.now() - timedelta(days=i*7),
                    "duration": 60,
                    "type": "meeting" if i % 2 == 0 else "focus_time"
                }
                for i in range(12)
            ]

        # TODO: Implement actual Calendar API integration
        return []

    def _analyze_schedule_patterns(self, events: List[Dict]) -> List[Dict]:
        """Analyze schedule patterns from events"""
        # Group events by day of week
        patterns = []

        # Example: Identify focus time patterns
        patterns.append({
            "pattern": "prefers_morning_focus",
            "confidence": 0.8,
            "evidence": "Most focus blocks scheduled 9-11am"
        })

        patterns.append({
            "pattern": "meeting_heavy_tuesdays",
            "confidence": 0.7,
            "evidence": "Average 4 meetings on Tuesdays"
        })

        return patterns

    def _analyze_energy_patterns(self, events: List[Dict]) -> List[Dict]:
        """Analyze energy patterns from calendar"""
        return [
            {
                "time_of_day": "morning",
                "energy_level": "high",
                "best_for": "creative_work"
            },
            {
                "day_of_week": "friday",
                "energy_level": "medium",
                "best_for": "planning"
            }
        ]

    def _scan_local_repositories(self) -> List[Dict]:
        """Scan for local git repositories"""
        repos = []

        # Check common project locations
        project_paths = [
            os.path.expanduser("~"),
            os.path.join(os.path.expanduser("~"), "projects"),
            os.path.join(os.path.expanduser("~"), "code")
        ]

        for path in project_paths:
            if os.path.exists(path):
                # Find .git directories
                for root, dirs, files in os.walk(path):
                    if '.git' in dirs:
                        repos.append({
                            "name": os.path.basename(root),
                            "path": root,
                            "type": "git"
                        })
                        # Don't recurse into git repos
                        dirs.remove('.git')

        return repos[:10]  # Limit to 10 for now

    def _analyze_coding_style(self, repo: Dict) -> Dict:
        """Analyze coding style from repository"""
        return {
            "repo_name": repo.get("name"),
            "primary_language": "python",  # TODO: Detect from files
            "code_style": "clean",
            "documentation_level": "moderate"
        }

    def _analyze_project_pattern(self, repo: Dict) -> Dict:
        """Analyze project patterns"""
        return {
            "repo_name": repo.get("name"),
            "project_type": "automation",
            "complexity": "medium",
            "active": True
        }

    def _scan_project_directories(self, projects_folder: str) -> List[str]:
        """Scan project directories"""
        projects = []

        if os.path.exists(projects_folder):
            for item in os.listdir(projects_folder):
                item_path = os.path.join(projects_folder, item)
                if os.path.isdir(item_path):
                    projects.append(item_path)

        return projects

    def _analyze_project_status(self, project_path: str) -> Dict:
        """Analyze project status"""
        return {
            "name": os.path.basename(project_path),
            "path": project_path,
            "status": "active",  # TODO: Detect from git activity
            "last_modified": datetime.now().isoformat()
        }

    def _analyze_project_dependencies(self, projects: List[str]) -> Dict:
        """Analyze dependencies between projects"""
        return {
            "dependency_count": len(projects),
            "interconnected": False
        }

    def _fetch_conversations(self, conversation_db) -> List[Dict]:
        """Fetch past conversations"""
        # TODO: Query actual database
        return []

    def _analyze_thinking_pattern(self, conversation: Dict) -> Optional[Dict]:
        """Analyze thinking patterns from conversation"""
        return {
            "pattern_type": "analytical",
            "evidence": "Asks clarifying questions before decisions"
        }

    def _extract_feedback(self, conversation: Dict) -> Optional[Dict]:
        """Extract feedback from conversation"""
        return None

    def _retrieve_all_cognitive_data(self) -> List[Dict]:
        """Retrieve all stored cognitive data"""
        # TODO: Query database
        return []

    def _synthesize_working_style(self, data: List[Dict]) -> Dict:
        """Synthesize working style from data"""
        return {
            "best_hours": "9am-11am",
            "focus_preference": "deep_work_blocks",
            "interruption_tolerance": "low"
        }

    def _synthesize_communication_style(self, data: List[Dict]) -> Dict:
        """Synthesize communication style"""
        return {
            "preferred_channel": "async",
            "response_time": "quick",
            "tone": "professional_friendly"
        }

    def _infer_values(self, data: List[Dict]) -> List[str]:
        """Infer values from data"""
        return ["autonomy", "efficiency", "privacy", "learning"]

    def _identify_patterns(self, data: List[Dict]) -> List[Dict]:
        """Identify patterns from data"""
        return [
            {"pattern": "works_best_mornings", "confidence": 0.8},
            {"pattern": "prefers_written_communication", "confidence": 0.7}
        ]

    def _extract_preferences(self, data: List[Dict]) -> Dict:
        """Extract preferences"""
        return {
            "notification_style": "minimal",
            "automation_level": "high",
            "approval_frequency": "important_actions_only"
        }

    def _store_cognitive_data(self, data_type: str, source: str, content: Dict,
                            timestamp: datetime, relevance_score: float = 0.8):
        """
        Store cognitive data in database and vector store

        Args:
            data_type: Type of cognitive data
            source: Data source
            content: Content dict
            timestamp: When data was created
            relevance_score: Relevance score (0-1)
        """
        try:
            # Encrypt sensitive content
            encrypted_content = self.encryption.encrypt(json.dumps(content))

            # Generate embedding for vector search
            embedding_text = self._generate_embedding_text(data_type, content)
            embedding_id = self._store_embedding(embedding_text, {
                "data_type": data_type,
                "source": source,
                "timestamp": timestamp.isoformat() if timestamp else None
            })

            # Store in database
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO cognitive_data
                (data_type, source, content, embedding_id, timestamp, relevance_score)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (data_type, source, encrypted_content, embedding_id, timestamp, relevance_score))
            self.db.commit()

        except Exception as e:
            self.logger.error(f"Error storing cognitive data: {e}")
            raise

    def _store_cognitive_profile(self, profile: Dict):
        """Store cognitive profile in database"""
        try:
            cursor = self.db.cursor()

            for attribute, value in profile.items():
                if attribute == "generated_at":
                    continue

                cursor.execute("""
                    INSERT INTO cognitive_profile
                    (attribute, confidence, source, last_updated)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (attribute)
                    DO UPDATE SET
                        confidence = EXCLUDED.confidence,
                        source = EXCLUDED.source,
                        last_updated = EXCLUDED.last_updated
                """, (attribute, 0.8, "synthesized", datetime.now()))

            self.db.commit()

        except Exception as e:
            self.logger.error(f"Error storing cognitive profile: {e}")
            raise

    def _generate_embedding_text(self, data_type: str, content: Dict) -> str:
        """Generate text for embedding from content"""
        # Create searchable text representation
        return f"{data_type}: {json.dumps(content)}"

    def _store_embedding(self, text: str, metadata: Dict) -> str:
        """Store embedding in vector store and return ID"""
        # Generate unique ID
        embedding_id = hashlib.md5(text.encode()).hexdigest()

        # TODO: Actually store in vector store (Chroma)
        # For now, just return the ID
        return embedding_id
