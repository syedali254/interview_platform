"""Module 3 — Skill Knowledge Graph using ESCO Taxonomy (EU Standard).

Builds a NetworkX DiGraph from ESCO digital skills collection (1,201 IT skills).
Maps candidate CV skills and job requirements to the ESCO taxonomy, then performs
gap analysis and generates interview topics.
"""

import networkx as nx
import pandas as pd
from difflib import get_close_matches
from pathlib import Path

# Path to ESCO data files
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "esco"


class SkillGraph:
    """ESCO-based skill knowledge graph with gap analysis capabilities."""

    def __init__(self):
        self.G = nx.DiGraph()
        self._label_to_uri = {}       # lowercase label -> URI
        self._uri_to_label = {}       # URI -> preferred label
        self._alt_labels = {}         # lowercase alt label -> URI
        self._categories = {}         # URI -> category name
        self._candidate_uris = set()
        self._required_uris = set()
        self._nice_uris = set()
        self._load_esco_taxonomy()

    def _load_esco_taxonomy(self):
        """Load ESCO digital skills + supplementary modern tech stack into the graph."""
        skills_path = DATA_DIR / "digitalSkillsCollection_en.csv"
        if not skills_path.exists():
            raise FileNotFoundError(f"ESCO data not found at {skills_path}")

        df = pd.read_csv(skills_path)

        # Add ESCO skill nodes
        for _, row in df.iterrows():
            uri = row["conceptUri"]
            label = str(row["preferredLabel"]).strip()
            category = str(row.get("broaderConceptPT", "")).strip()
            skill_type = str(row.get("skillType", "")).strip()

            self.G.add_node(uri, label=label, category=category,
                           skill_type=skill_type, type="skill")

            # Build lookup indexes
            self._label_to_uri[label.lower()] = uri
            self._uri_to_label[uri] = label

            if category:
                self._categories[uri] = category

            # Index alternative labels for fuzzy matching
            alt = row.get("altLabels", "")
            if pd.notna(alt):
                for alt_label in str(alt).split("\n"):
                    alt_label = alt_label.strip()
                    if alt_label:
                        self._alt_labels[alt_label.lower()] = uri

            # Add category node and edge
            if category:
                cat_node = f"cat:{category}"
                if cat_node not in self.G:
                    self.G.add_node(cat_node, label=category, type="category")
                self.G.add_edge(cat_node, uri, relation="contains")

        # Load broader relations for hierarchy edges between skills
        relations_path = DATA_DIR / "broaderRelationsSkillPillar.csv"
        if relations_path.exists():
            rel_df = pd.read_csv(relations_path)
            digital_uris = set(df["conceptUri"])
            for _, row in rel_df.iterrows():
                child = row.get("conceptUri", "")
                parent = row.get("broaderUri", "")
                if child in digital_uris and parent in digital_uris:
                    self.G.add_edge(parent, child, relation="broader")

        # ─── Supplementary Modern Tech Stack Extension ────────────────────
        # ESCO (v1.1.1) lacks many modern tools/frameworks. We extend with
        # industry-standard technologies commonly found in job descriptions.
        # This extension is categorized to align with ESCO's structure.
        self._load_tech_extension()

    def _load_tech_extension(self):
        """Add modern technology stack that ESCO doesn't yet include."""
        TECH_EXTENSION = {
            # Cloud Platforms
            "cloud platforms & infrastructure": [
                "AWS", "Azure", "GCP", "Heroku", "DigitalOcean",
                "AWS Lambda", "EC2", "S3", "CloudFormation",
            ],
            # Containers & Orchestration
            "containerization & orchestration": [
                "Docker", "Kubernetes", "Docker Compose", "Helm",
                "Container Registry", "Podman",
            ],
            # DevOps & CI/CD
            "devops & ci/cd": [
                "CI/CD", "Jenkins", "GitHub Actions", "GitLab CI",
                "Terraform", "Ansible", "ArgoCD", "Prometheus", "Grafana",
            ],
            # Backend Frameworks
            "backend frameworks": [
                "FastAPI", "Django", "Flask", "Express.js", "NestJS",
                "Spring Boot", "Ruby on Rails", "ASP.NET Core", "Gin",
            ],
            # Frontend Frameworks
            "frontend frameworks": [
                "React", "Angular", "Vue.js", "Next.js", "Svelte",
                "Tailwind CSS", "Bootstrap", "Material UI",
            ],
            # JavaScript Runtime & Tools
            "javascript ecosystem": [
                "Node.js", "TypeScript", "Deno", "Bun", "NPM", "Webpack",
                "Vite", "ESLint",
            ],
            # Databases
            "databases & data stores": [
                "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
                "DynamoDB", "Cassandra", "Neo4j", "InfluxDB",
            ],
            # Message Queues & Streaming
            "messaging & event streaming": [
                "Kafka", "RabbitMQ", "Apache Pulsar", "Redis Streams",
                "Amazon SQS", "NATS",
            ],
            # AI/ML Frameworks
            "ai & machine learning tools": [
                "TensorFlow", "PyTorch", "scikit-learn", "Keras",
                "Hugging Face", "LangChain", "LlamaIndex", "OpenAI API",
                "Pandas", "NumPy", "XGBoost", "LightGBM",
            ],
            # Architecture Patterns
            "architecture & design patterns": [
                "Microservices", "REST API", "GraphQL", "gRPC",
                "Event-Driven Architecture", "CQRS", "Domain-Driven Design",
                "System Design",
            ],
            # Version Control & Collaboration
            "version control & collaboration": [
                "Git", "GitHub", "GitLab", "Bitbucket",
            ],
            # API & Integration
            "api & integration": [
                "REST", "GraphQL", "WebSocket", "OAuth", "JWT",
                "API Gateway", "Swagger/OpenAPI",
            ],
            # Testing
            "testing & quality assurance": [
                "Jest", "Pytest", "Selenium", "Cypress", "JUnit",
                "Unit Testing", "Integration Testing", "TDD",
            ],
            # Data Engineering
            "data engineering": [
                "Apache Spark", "Airflow", "dbt", "ETL",
                "Data Pipeline", "Data Warehouse", "Snowflake",
            ],
        }

        for category, skills in TECH_EXTENSION.items():
            cat_uri = f"ext:cat:{category}"
            self.G.add_node(cat_uri, label=category.title(), type="category")

            for skill in skills:
                skill_uri = f"ext:{skill.lower().replace(' ', '_')}"
                self.G.add_node(skill_uri, label=skill, category=category,
                               type="skill", source="extension")
                self.G.add_edge(cat_uri, skill_uri, relation="contains")

                # Index for matching
                self._label_to_uri[skill.lower()] = skill_uri
                self._uri_to_label[skill_uri] = skill

                # Add common abbreviations/aliases
                aliases = _get_aliases(skill)
                for alias in aliases:
                    self._alt_labels[alias.lower()] = skill_uri

    def match_skill(self, skill_text: str) -> str | None:
        """Match a free-text skill name to an ESCO URI using fuzzy matching."""
        text = skill_text.lower().strip()

        # Exact match on preferred label
        if text in self._label_to_uri:
            return self._label_to_uri[text]

        # Exact match on alt labels
        if text in self._alt_labels:
            return self._alt_labels[text]

        # Fuzzy match on preferred labels (cutoff 0.75)
        all_labels = list(self._label_to_uri.keys())
        matches = get_close_matches(text, all_labels, n=1, cutoff=0.75)
        if matches:
            return self._label_to_uri[matches[0]]

        # Fuzzy match on alt labels (cutoff 0.8)
        alt_list = list(self._alt_labels.keys())
        matches = get_close_matches(text, alt_list, n=1, cutoff=0.8)
        if matches:
            return self._alt_labels[matches[0]]

        # Partial substring match (for skills like "React" matching "React (JavaScript framework)")
        for label, uri in self._label_to_uri.items():
            if text in label or label in text:
                return uri

        return None

    def add_candidate_skills(self, skills: list):
        """Map and add candidate's skills to the graph."""
        for skill_text in skills:
            uri = self.match_skill(skill_text)
            if uri and uri in self.G:
                self.G.nodes[uri]["has"] = True
                self._candidate_uris.add(uri)
            else:
                # Add as unmatched skill node
                custom_uri = f"custom:candidate:{skill_text.lower().strip()}"
                self.G.add_node(custom_uri, label=skill_text, type="unmatched",
                               has=True, category="Unmatched")
                self._candidate_uris.add(custom_uri)

    def add_job_skills(self, required: list, nice_to_have: list = None):
        """Map and add job requirement skills to the graph."""
        for skill_text in required:
            uri = self.match_skill(skill_text)
            if uri and uri in self.G:
                self.G.nodes[uri]["required"] = True
                self._required_uris.add(uri)
            else:
                custom_uri = f"custom:required:{skill_text.lower().strip()}"
                self.G.add_node(custom_uri, label=skill_text, type="unmatched",
                               required=True, category="Unmatched")
                self._required_uris.add(custom_uri)

        for skill_text in (nice_to_have or []):
            uri = self.match_skill(skill_text)
            if uri and uri in self.G:
                self.G.nodes[uri]["nice"] = True
                self._nice_uris.add(uri)
            else:
                custom_uri = f"custom:nice:{skill_text.lower().strip()}"
                self.G.add_node(custom_uri, label=skill_text, type="unmatched",
                               nice=True, category="Unmatched")
                self._nice_uris.add(custom_uri)

    def analyse_gaps(self) -> dict:
        """Perform gap analysis between candidate skills and job requirements."""
        matched_req = sorted(
            [self._get_label(u) for u in self._candidate_uris & self._required_uris]
        )
        missing_req = sorted(
            [self._get_label(u) for u in self._required_uris - self._candidate_uris]
        )
        matched_nice = sorted(
            [self._get_label(u) for u in self._candidate_uris & self._nice_uris]
        )
        missing_nice = sorted(
            [self._get_label(u) for u in self._nice_uris - self._candidate_uris]
        )
        extra = sorted(
            [self._get_label(u) for u in
             self._candidate_uris - self._required_uris - self._nice_uris]
        )

        total_req = max(len(self._required_uris), 1)
        pct = round(len(self._candidate_uris & self._required_uris) / total_req * 100, 1)

        return {
            "match_percentage": pct,
            "matched_required": matched_req,
            "missing_required": missing_req,
            "matched_nice_to_have": matched_nice,
            "missing_nice_to_have": missing_nice,
            "extra_skills": extra,
            "total_candidate": len(self._candidate_uris),
            "total_required": len(self._required_uris),
            "esco_matched_count": len(
                [u for u in self._candidate_uris | self._required_uris | self._nice_uris
                 if not u.startswith("custom:")]
            ),
        }

    def get_interview_topics(self, max_topics: int = 8) -> list:
        """Generate prioritised interview topics from gap analysis."""
        gaps = self.analyse_gaps()
        topics = []

        for s in gaps["missing_required"][:3]:
            topics.append({
                "skill": s, "reason": "Required but not on CV — assess if learnable",
                "priority": "high"
            })
        for s in gaps["matched_required"][:3]:
            topics.append({
                "skill": s, "reason": "Listed on CV — verify depth of knowledge",
                "priority": "medium"
            })
        for s in gaps["matched_nice_to_have"][:2]:
            topics.append({
                "skill": s, "reason": "Bonus skill present — explore proficiency",
                "priority": "low"
            })

        return topics[:max_topics]

    def get_stats(self) -> dict:
        """Return graph statistics."""
        return {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "candidate_skills": len(self._candidate_uris),
            "job_required": len(self._required_uris),
            "job_nice": len(self._nice_uris),
            "esco_taxonomy_size": len(self._label_to_uri),
        }

    def get_skill_categories(self) -> dict:
        """Get skills grouped by ESCO category for visualization."""
        result = {"candidate": {}, "required": {}, "nice": {}}

        for uri in self._candidate_uris:
            cat = self._get_category(uri)
            result["candidate"].setdefault(cat, []).append(self._get_label(uri))

        for uri in self._required_uris:
            cat = self._get_category(uri)
            result["required"].setdefault(cat, []).append(self._get_label(uri))

        for uri in self._nice_uris:
            cat = self._get_category(uri)
            result["nice"].setdefault(cat, []).append(self._get_label(uri))

        return result

    def _get_label(self, uri: str) -> str:
        """Get human-readable label for a URI."""
        if uri in self.G:
            return self.G.nodes[uri].get("label", uri)
        return uri.split(":")[-1]

    def _get_category(self, uri: str) -> str:
        """Get the ESCO category for a skill URI."""
        if uri in self.G:
            cat = self.G.nodes[uri].get("category", "")
            if cat and cat != "Unmatched":
                # Shorten long ESCO category names
                parts = cat.split(" | ")
                return parts[0][:40] if parts else cat[:40]
        return "Other"


def build_graph(cv_data: dict, jd_data: dict) -> SkillGraph:
    """Build a complete ESCO skill graph from parsed CV and JD."""
    sg = SkillGraph()
    sg.add_candidate_skills(cv_data.get("skills", []))
    sg.add_job_skills(
        jd_data.get("required_skills", []),
        jd_data.get("nice_to_have", []),
    )
    return sg


def _get_aliases(skill: str) -> list:
    """Return common aliases/abbreviations for a tech skill."""
    ALIAS_MAP = {
        "AWS": ["amazon web services", "amazon aws"],
        "GCP": ["google cloud platform", "google cloud"],
        "Azure": ["microsoft azure", "azure cloud"],
        "Docker": ["docker containers", "docker engine"],
        "Kubernetes": ["k8s"],
        "CI/CD": ["cicd", "continuous integration", "continuous deployment",
                   "ci cd", "ci-cd"],
        "PostgreSQL": ["postgres", "psql"],
        "MongoDB": ["mongo"],
        "Node.js": ["nodejs", "node"],
        "React": ["reactjs", "react.js"],
        "Vue.js": ["vuejs", "vue"],
        "Angular": ["angularjs"],
        "TypeScript": ["ts"],
        "JavaScript": ["js"],
        "Express.js": ["express", "expressjs"],
        "Next.js": ["nextjs"],
        "REST API": ["restful api", "rest apis", "restful"],
        "GraphQL": ["graph ql"],
        "TensorFlow": ["tf"],
        "PyTorch": ["pytorch framework"],
        "scikit-learn": ["sklearn", "scikit learn"],
        "Pandas": ["python pandas"],
        "NumPy": ["numpy", "python numpy"],
        "Machine Learning": ["ml"],
        "Deep Learning": ["dl"],
        "FastAPI": ["fast api"],
        "Django": ["django framework", "python django"],
        "Flask": ["python flask"],
        "Spring Boot": ["springboot", "spring-boot"],
        "Docker Compose": ["docker-compose"],
        "Terraform": ["terraform iac", "hashicorp terraform"],
        "Kafka": ["apache kafka"],
        "RabbitMQ": ["rabbit mq"],
        "Elasticsearch": ["elastic search", "elastic"],
        "GitHub Actions": ["gh actions"],
        "Hugging Face": ["huggingface", "hf"],
        "LangChain": ["langchain framework"],
        "Redis": ["redis cache"],
        "Microservices": ["micro services", "microservice architecture"],
        "Git": ["git vcs"],
        "XGBoost": ["xg boost"],
        "LightGBM": ["light gbm", "lightgbm"],
        "Tailwind CSS": ["tailwind", "tailwindcss"],
    }
    return ALIAS_MAP.get(skill, [])
