"""Module 3 — Skill Knowledge Graph using the ESCO taxonomy (EU standard).

Builds a NetworkX DiGraph from the ESCO digital skills collection (1,201 IT
skills) and extends it with a modern technology stack and a soft-skill
taxonomy that ESCO v1.1.1 does not cover. Candidate CV skills and job
requirements are mapped onto that taxonomy, then compared to produce gap
analysis, interview topics, and a graph payload the UI renders directly.

Matching is deliberately conservative. A skill is mapped only when it:
  1. matches a preferred label exactly, or
  2. matches a known alias/abbreviation exactly, or
  3. matches the base form of a parenthesised ESCO label
     ("python" -> "Python (computer programming)"), or
  4. is a close fuzzy match on a string long enough for fuzzy matching to
     be meaningful.

Anything else becomes its own node rather than being forced onto an unrelated
concept. An earlier version used a bare substring fallback, which mapped
"Team Leadership" onto the ESCO skill "R" and "Communication" onto
"telecommunications engineering"; that fallback is gone.
"""

import re
from difflib import get_close_matches
from pathlib import Path

import networkx as nx
import pandas as pd

# Path to ESCO data files
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "esco"

# Node statuses used by the UI and the gap analysis
STATUS_MATCHED = "matched"              # candidate has it and the job requires it
STATUS_MISSING = "missing"              # job requires it, candidate lacks it
STATUS_BONUS = "bonus"                  # candidate has a nice-to-have
STATUS_BONUS_MISSING = "bonus_missing"  # nice-to-have the candidate lacks
STATUS_EXTRA = "extra"                  # candidate has it, job does not ask for it

# Fuzzy matching is only meaningful on reasonably long strings. Short labels
# such as "R", "C#" or "SQL" must match exactly or not at all.
MIN_FUZZY_LEN = 6
FUZZY_CUTOFF = 0.88

_PAREN_RE = re.compile(r"\s*\([^)]*\)")
_PUNCT_RE = re.compile(r"[^a-z0-9+#./ -]")
_SPACE_RE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Lowercase, strip punctuation noise and collapse whitespace."""
    t = str(text).lower().strip()
    t = _PUNCT_RE.sub(" ", t)
    return _SPACE_RE.sub(" ", t).strip()


def base_form(label: str) -> str:
    """Strip a trailing parenthetical qualifier from an ESCO label."""
    return _PAREN_RE.sub("", str(label)).strip()


def display_name(label: str) -> str:
    """Human-facing form of a label: no parenthetical, leading capital."""
    clean = base_form(label)
    if not clean:
        return str(label)
    return clean[0].upper() + clean[1:]


class SkillGraph:
    """ESCO-based skill knowledge graph with gap analysis capabilities."""

    def __init__(self):
        self.G = nx.DiGraph()
        self._label_to_uri = {}    # normalised preferred label -> URI
        self._alt_labels = {}      # normalised alias/base form -> URI
        self._fuzzy_pool = []      # normalised labels eligible for fuzzy matching

        self._candidate_uris = set()
        self._required_uris = set()
        self._nice_uris = set()

        # Original input text -> resolved URI, so we can report how many raw
        # skills were supplied even when several of them resolve to one node.
        self._candidate_inputs = {}
        self._required_inputs = {}
        self._nice_inputs = {}

        self._load_esco_taxonomy()

    # ── Taxonomy loading ──────────────────────────────────────────────────

    def _load_esco_taxonomy(self):
        """Load ESCO digital skills plus supplementary taxonomies."""
        skills_path = DATA_DIR / "digitalSkillsCollection_en.csv"
        if not skills_path.exists():
            raise FileNotFoundError(f"ESCO data not found at {skills_path}")

        df = pd.read_csv(skills_path)

        for _, row in df.iterrows():
            uri = row["conceptUri"]
            label = str(row["preferredLabel"]).strip()
            category = self._clean_category(row.get("broaderConceptPT", ""))

            self.G.add_node(
                uri,
                label=display_name(label),
                esco_label=label,
                category=category,
                skill_type=str(row.get("skillType", "")).strip(),
                type="skill",
                source="esco",
            )

            self._index(normalise(label), uri, preferred=True)

            # Index the base form so "Python" reaches
            # "Python (computer programming)" without a substring search.
            base = normalise(base_form(label))
            if base and base != normalise(label):
                self._index(base, uri)

            alt = row.get("altLabels", "")
            if pd.notna(alt):
                for alt_label in str(alt).split("\n"):
                    if alt_label.strip():
                        self._index(normalise(alt_label), uri)

            if category:
                cat_node = f"cat:{category}"
                if cat_node not in self.G:
                    self.G.add_node(cat_node, label=display_name(category),
                                    type="category")
                self.G.add_edge(cat_node, uri, relation="contains")

        # Real ESCO hierarchy edges between digital skills
        relations_path = DATA_DIR / "broaderRelationsSkillPillar.csv"
        if relations_path.exists():
            rel_df = pd.read_csv(relations_path)
            digital_uris = set(df["conceptUri"])
            for _, row in rel_df.iterrows():
                child = row.get("conceptUri", "")
                parent = row.get("broaderUri", "")
                if child in digital_uris and parent in digital_uris:
                    self.G.add_edge(parent, child, relation="broader")

        self._load_extension(TECH_EXTENSION, prefix="tech")
        self._load_extension(SOFT_SKILL_EXTENSION, prefix="soft")

        # Build the fuzzy pool once, after every label is indexed.
        self._fuzzy_pool = [
            label for label in self._label_to_uri
            if len(label) >= MIN_FUZZY_LEN
        ]

    def _index(self, key: str, uri: str, preferred: bool = False):
        """Register a lookup key, without letting aliases shadow real labels."""
        if not key:
            return
        if preferred:
            self._label_to_uri.setdefault(key, uri)
            return
        # An alias must never override an exact preferred label.
        if key in self._label_to_uri:
            return
        self._alt_labels.setdefault(key, uri)

    def _load_extension(self, taxonomy: dict, prefix: str):
        """Add a supplementary taxonomy ESCO does not cover."""
        for category, skills in taxonomy.items():
            cat_uri = f"{prefix}:cat:{category}"
            self.G.add_node(cat_uri, label=display_name(category), type="category")

            for skill in skills:
                skill_uri = f"{prefix}:{normalise(skill).replace(' ', '_')}"
                self.G.add_node(
                    skill_uri,
                    label=skill,
                    esco_label=skill,
                    category=category,
                    type="skill",
                    source="extension",
                )
                self.G.add_edge(cat_uri, skill_uri, relation="contains")

                # Extension labels take precedence: they are the modern,
                # recognisable form of the concept ("Docker", "Leadership").
                self._label_to_uri[normalise(skill)] = skill_uri
                for alias in ALIAS_MAP.get(skill, []):
                    self._alt_labels[normalise(alias)] = skill_uri

    @staticmethod
    def _clean_category(raw) -> str:
        """ESCO categories are pipe-separated; keep the first, trimmed."""
        if not raw or pd.isna(raw):
            return ""
        return str(raw).split(" | ")[0].strip()

    # ── Matching ──────────────────────────────────────────────────────────

    def match_skill(self, skill_text: str) -> str | None:
        """Map free text to a taxonomy URI, or None when there is no safe match."""
        text = normalise(skill_text)
        if not text:
            return None

        if text in self._label_to_uri:
            return self._label_to_uri[text]
        if text in self._alt_labels:
            return self._alt_labels[text]

        # Fuzzy matching, only for strings long enough to be meaningful.
        if len(text) >= MIN_FUZZY_LEN:
            hit = get_close_matches(text, self._fuzzy_pool, n=1, cutoff=FUZZY_CUTOFF)
            if hit:
                return self._label_to_uri[hit[0]]

        return None

    def _resolve(self, skill_text: str) -> str:
        """Return the URI for a skill, creating a custom node when unmatched.

        Unmatched skills share one namespace across the CV and the JD, so a
        skill ESCO does not know about still registers as a match when it
        appears on both sides.
        """
        uri = self.match_skill(skill_text)
        if uri and uri in self.G:
            return uri

        key = normalise(skill_text)
        custom_uri = f"custom:{key}"
        if custom_uri not in self.G:
            self.G.add_node(
                custom_uri,
                label=display_name(skill_text),
                esco_label=str(skill_text).strip(),
                category="Other / Not in taxonomy",
                type="skill",
                source="unmatched",
            )
        return custom_uri

    # ── Population ────────────────────────────────────────────────────────

    def add_candidate_skills(self, skills: list):
        """Map and add the candidate's skills to the graph."""
        for skill_text in skills or []:
            if not isinstance(skill_text, str) or not skill_text.strip():
                continue
            uri = self._resolve(skill_text)
            self.G.nodes[uri]["has"] = True
            self._candidate_uris.add(uri)
            self._candidate_inputs[skill_text.strip()] = uri

    def add_job_skills(self, required: list, nice_to_have: list = None):
        """Map and add job requirement skills to the graph."""
        for skill_text in required or []:
            if not isinstance(skill_text, str) or not skill_text.strip():
                continue
            uri = self._resolve(skill_text)
            self.G.nodes[uri]["required"] = True
            self._required_uris.add(uri)
            self._required_inputs[skill_text.strip()] = uri

        for skill_text in nice_to_have or []:
            if not isinstance(skill_text, str) or not skill_text.strip():
                continue
            uri = self._resolve(skill_text)
            self.G.nodes[uri]["nice"] = True
            self._nice_uris.add(uri)
            self._nice_inputs[skill_text.strip()] = uri

    # ── Analysis ──────────────────────────────────────────────────────────

    def status_map(self) -> dict:
        """URI -> status for every skill involved in this comparison."""
        statuses = {}
        # Applied least-specific first so the strongest status wins.
        for uri in self._candidate_uris - self._required_uris - self._nice_uris:
            statuses[uri] = STATUS_EXTRA
        for uri in self._nice_uris - self._candidate_uris - self._required_uris:
            statuses[uri] = STATUS_BONUS_MISSING
        for uri in self._candidate_uris & self._nice_uris:
            statuses[uri] = STATUS_BONUS
        for uri in self._required_uris - self._candidate_uris:
            statuses[uri] = STATUS_MISSING
        for uri in self._candidate_uris & self._required_uris:
            statuses[uri] = STATUS_MATCHED
        return statuses

    def analyse_gaps(self) -> dict:
        """Compare candidate skills against job requirements."""
        def labels(uris):
            return sorted({self._get_label(u) for u in uris}, key=str.lower)

        matched = self._candidate_uris & self._required_uris
        missing = self._required_uris - self._candidate_uris
        matched_nice = self._candidate_uris & self._nice_uris
        missing_nice = self._nice_uris - self._candidate_uris - self._required_uris
        extra = self._candidate_uris - self._required_uris - self._nice_uris

        total_req = max(len(self._required_uris), 1)
        pct = round(len(matched) / total_req * 100, 1)

        involved = self._candidate_uris | self._required_uris | self._nice_uris
        return {
            "match_percentage": pct,
            "matched_required": labels(matched),
            "missing_required": labels(missing),
            "matched_nice_to_have": labels(matched_nice),
            "missing_nice_to_have": labels(missing_nice),
            "extra_skills": labels(extra),
            "total_candidate": len(self._candidate_uris),
            "total_required": len(self._required_uris),
            "esco_matched_count": len(
                [u for u in involved if not u.startswith("custom:")]
            ),
            "unmatched_count": len(
                [u for u in involved if u.startswith("custom:")]
            ),
        }

    def get_interview_topics(self, max_topics: int = 8) -> list:
        """Generate prioritised interview topics from the gap analysis."""
        gaps = self.analyse_gaps()
        topics = []
        seen = set()

        def add(skill, reason, priority):
            key = skill.lower()
            if key in seen:
                return
            seen.add(key)
            topics.append({"skill": skill, "reason": reason, "priority": priority})

        for s in gaps["missing_required"][:3]:
            add(s, "Required but not on CV — assess if learnable", "high")
        for s in gaps["matched_required"][:3]:
            add(s, "Listed on CV — verify depth of knowledge", "medium")
        for s in gaps["matched_nice_to_have"][:2]:
            add(s, "Bonus skill present — explore proficiency", "low")

        return topics[:max_topics]

    def get_stats(self) -> dict:
        """Return graph statistics."""
        return {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "candidate_skills": len(self._candidate_uris),
            "candidate_skills_supplied": len(self._candidate_inputs),
            "job_required": len(self._required_uris),
            "job_nice": len(self._nice_uris),
            "taxonomy_size": len(self._label_to_uri),
        }

    def to_graph_payload(self) -> dict:
        """Node-link graph grouped by category, ready for the UI to render.

        Each cluster is one category hub plus its skills. Hierarchy edges are
        the real ESCO 'broader' relations between skills that are in play.
        """
        statuses = self.status_map()

        clusters = {}
        for uri, status in statuses.items():
            category = self._get_category(uri)
            clusters.setdefault(category, []).append({
                "id": uri,
                "label": self._get_label(uri),
                "status": status,
                "source": self.G.nodes[uri].get("source", "esco"),
            })

        # Real taxonomy edges between the skills on screen.
        in_play = set(statuses)
        hierarchy = [
            {"source": u, "target": v}
            for u, v, d in self.G.edges(data=True)
            if d.get("relation") == "broader" and u in in_play and v in in_play
        ]

        cluster_list = [
            {
                "category": category,
                "skills": sorted(skills, key=lambda s: (s["status"], s["label"].lower())),
            }
            for category, skills in clusters.items()
        ]
        # Biggest, most relevant clusters first.
        cluster_list.sort(
            key=lambda c: (
                -sum(1 for s in c["skills"] if s["status"] in (STATUS_MATCHED, STATUS_MISSING)),
                -len(c["skills"]),
                c["category"].lower(),
            )
        )

        counts = {}
        for status in statuses.values():
            counts[status] = counts.get(status, 0) + 1

        return {
            "clusters": cluster_list,
            "hierarchy_edges": hierarchy,
            "counts": counts,
            "total_nodes": len(statuses),
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get_label(self, uri: str) -> str:
        if uri in self.G:
            return self.G.nodes[uri].get("label", uri)
        return uri.split(":")[-1]

    def _get_category(self, uri: str) -> str:
        if uri in self.G:
            cat = self.G.nodes[uri].get("category", "")
            if cat:
                return display_name(cat)
        return "Other"


def build_graph(cv_data: dict, jd_data: dict) -> SkillGraph:
    """Build a complete ESCO skill graph from a parsed CV and JD."""
    sg = SkillGraph()
    sg.add_candidate_skills(cv_data.get("skills", []))
    sg.add_job_skills(
        jd_data.get("required_skills", []),
        jd_data.get("nice_to_have", []),
    )
    return sg


# ─── Supplementary taxonomies ────────────────────────────────────────────────
# ESCO v1.1.1 predates most of the modern stack and covers soft skills only
# sparsely. These extensions are categorised to mirror ESCO's own structure.

TECH_EXTENSION = {
    "Cloud Platforms & Infrastructure": [
        "AWS", "Azure", "GCP", "Heroku", "DigitalOcean",
        "AWS Lambda", "EC2", "S3", "CloudFormation",
    ],
    "Containerisation & Orchestration": [
        "Docker", "Kubernetes", "Docker Compose", "Helm",
        "Container Registry", "Podman",
    ],
    "DevOps & CI/CD": [
        "CI/CD", "Jenkins", "GitHub Actions", "GitLab CI",
        "Terraform", "Ansible", "ArgoCD", "Prometheus", "Grafana",
    ],
    "Backend Frameworks": [
        "FastAPI", "Django", "Flask", "Express.js", "NestJS",
        "Spring Boot", "Ruby on Rails", "ASP.NET Core", "Gin",
    ],
    "Frontend Frameworks": [
        "React", "Angular", "Vue.js", "Next.js", "Svelte",
        "Tailwind CSS", "Bootstrap", "Material UI",
    ],
    "JavaScript Ecosystem": [
        "Node.js", "TypeScript", "Deno", "Bun", "NPM", "Webpack",
        "Vite", "ESLint",
    ],
    "Databases & Data Stores": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "Neo4j", "InfluxDB",
    ],
    "Messaging & Event Streaming": [
        "Kafka", "RabbitMQ", "Apache Pulsar", "Redis Streams",
        "Amazon SQS", "NATS",
    ],
    "AI & Machine Learning Tools": [
        "TensorFlow", "PyTorch", "scikit-learn", "Keras",
        "Hugging Face", "LangChain", "LlamaIndex", "OpenAI API",
        "Pandas", "NumPy", "XGBoost", "LightGBM",
    ],
    "Architecture & Design Patterns": [
        "Microservices", "REST API", "GraphQL", "gRPC",
        "Event-Driven Architecture", "CQRS", "Domain-Driven Design",
        "System Design",
    ],
    "Version Control & Collaboration": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence",
    ],
    "API & Integration": [
        "REST", "WebSocket", "OAuth", "JWT",
        "API Gateway", "Swagger/OpenAPI",
    ],
    "Testing & Quality Assurance": [
        "Jest", "Pytest", "Selenium", "Cypress", "JUnit",
        "Unit Testing", "Integration Testing", "TDD",
    ],
    "Data Engineering": [
        "Apache Spark", "Airflow", "dbt", "ETL",
        "Data Pipeline", "Data Warehouse", "Snowflake",
    ],
    "Office & Productivity Tools": [
        "Microsoft Excel", "Microsoft Word", "PowerPoint", "Google Sheets",
        "Power BI", "Tableau", "Looker",
    ],
}

SOFT_SKILL_EXTENSION = {
    "Communication & Collaboration": [
        "Communication", "Written Communication", "Presentation Skills",
        "Public Speaking", "Active Listening", "Teamwork",
        "Cross-Functional Collaboration", "Stakeholder Management",
        "Client Facing", "Negotiation",
    ],
    "Leadership & Management": [
        "Leadership", "Team Leadership", "Mentoring", "Coaching",
        "People Management", "Delegation", "Conflict Resolution",
        "Decision Making", "Strategic Thinking",
    ],
    "Problem Solving & Thinking": [
        "Problem Solving", "Critical Thinking", "Analytical Thinking",
        "Attention to Detail", "Creativity", "Innovation",
        "Research Skills", "Troubleshooting",
    ],
    "Personal Effectiveness": [
        "Time Management", "Organisation", "Adaptability", "Resilience",
        "Self Motivation", "Work Ethic", "Curiosity",
        "Continuous Learning", "Emotional Intelligence",
    ],
    "Ways of Working": [
        "Agile", "Scrum", "Kanban", "Waterfall", "Code Review",
        "Pair Programming", "Documentation", "Project Management",
        "Requirements Gathering",
    ],
}

# Common abbreviations and spelling variants, keyed by extension label.
ALIAS_MAP = {
    "AWS": ["amazon web services", "amazon aws"],
    "GCP": ["google cloud platform", "google cloud"],
    "Azure": ["microsoft azure", "azure cloud"],
    "Docker": ["docker containers", "docker engine"],
    "Kubernetes": ["k8s"],
    "CI/CD": ["cicd", "continuous integration", "continuous deployment",
              "ci cd", "ci-cd", "continuous delivery"],
    "PostgreSQL": ["postgres", "psql"],
    "MongoDB": ["mongo"],
    "Node.js": ["nodejs", "node"],
    "React": ["reactjs", "react.js"],
    "Vue.js": ["vuejs", "vue"],
    "Angular": ["angularjs"],
    "TypeScript": ["ts"],
    "Express.js": ["express", "expressjs"],
    "Next.js": ["nextjs"],
    "REST API": ["restful api", "rest apis", "restful", "rest services"],
    "GraphQL": ["graph ql"],
    "TensorFlow": ["tensor flow"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "Pandas": ["python pandas"],
    "NumPy": ["python numpy"],
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
    "Hugging Face": ["huggingface"],
    "Redis": ["redis cache"],
    "Microservices": ["micro services", "microservice architecture",
                      "microservices architecture"],
    "XGBoost": ["xg boost"],
    "LightGBM": ["light gbm", "lightgbm"],
    "Tailwind CSS": ["tailwind", "tailwindcss"],
    "Microsoft Excel": ["excel", "ms excel", "advanced excel"],
    "Microsoft Word": ["word", "ms word"],
    "PowerPoint": ["ms powerpoint", "powerpoints"],
    "Power BI": ["powerbi", "power-bi"],
    "Unit Testing": ["unit tests"],
    "Communication": ["communication skills", "verbal communication",
                      "strong communicator", "interpersonal skills"],
    "Teamwork": ["team work", "team player", "collaboration"],
    "Leadership": ["leadership skills"],
    "Team Leadership": ["team lead", "leading teams", "team management"],
    "Problem Solving": ["problem-solving", "problem solving skills"],
    "Critical Thinking": ["critical thought"],
    "Analytical Thinking": ["analytical skills", "analytical"],
    "Attention to Detail": ["detail oriented", "detail-oriented"],
    "Time Management": ["time-management", "prioritisation", "prioritization"],
    "Organisation": ["organization", "organisational skills",
                     "organizational skills"],
    "Adaptability": ["flexible", "flexibility"],
    "Continuous Learning": ["lifelong learning", "eager to learn",
                            "willingness to learn"],
    "Agile": ["agile methodology", "agile methodologies", "agile development"],
    "Scrum": ["scrum master", "scrum methodology"],
    "Project Management": ["project manager", "project delivery"],
    "Mentoring": ["mentorship", "mentoring juniors"],
    "Stakeholder Management": ["stakeholder engagement"],
}
