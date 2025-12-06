# PHASE 5: INTELLIGENCE FEATURES
## Detailed Implementation Guide

**Prerequisites**: 
- Phase 4 complete and validated
- Branch: `git checkout -b phase-5-intelligence develop`

**Tasks**: TODO.md #205-239

**Estimated Duration**: 3-4 hours

---

## 1. OBJECTIVES

By the end of Phase 5:
- [ ] Domain detection working (medical, CI, regulatory, academic)
- [ ] Auto-configuration loads correct settings per domain
- [ ] Cross-verification detects contradictions
- [ ] Confidence scoring implemented
- [ ] Learning updates source effectiveness
- [ ] Privacy recommendation includes reasoning

---

## 2. DOMAIN DETECTION

### 2.1 Keyword-Based Detection

**File**: `/backend/src/research_tool/agent/decisions/domain_detector.py`

```python
from typing import Optional
from research_tool.models.domain import DomainConfiguration


class DomainDetector:
    """Detect research domain from query."""
    
    DOMAIN_KEYWORDS = {
        "medical": [
            "patient", "treatment", "diagnosis", "clinical", "therapy",
            "disease", "symptoms", "medication", "healthcare", "hospital",
            "doctor", "nurse", "surgery", "prescription", "dose"
        ],
        "competitive_intelligence": [
            "company", "competitor", "market", "funding", "startup",
            "revenue", "acquisition", "CEO", "product launch", "strategy",
            "valuation", "IPO", "investment", "business model"
        ],
        "regulatory": [
            "regulation", "compliance", "law", "legal", "policy",
            "FDA", "EASA", "directive", "requirement", "certification",
            "license", "permit", "approval", "standard"
        ],
        "academic": [
            "research", "study", "paper", "journal", "publication",
            "hypothesis", "methodology", "experiment", "theory", "peer-reviewed"
        ]
    }
    
    def detect(self, query: str) -> tuple[str, float]:
        """
        Detect domain from query.
        
        Returns: (domain, confidence)
        """
        query_lower = query.lower()
        scores = {}
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            scores[domain] = matches / len(keywords)
        
        if not scores or max(scores.values()) == 0:
            return "general", 0.0
        
        best_domain = max(scores, key=scores.get)
        confidence = scores[best_domain]
        
        # Require minimum confidence
        if confidence < 0.1:
            return "general", confidence
        
        return best_domain, confidence
    
    async def detect_with_llm(
        self,
        query: str,
        llm_router
    ) -> tuple[str, float, str]:
        """
        Use LLM for domain detection when keyword method uncertain.
        
        Returns: (domain, confidence, reasoning)
        """
        prompt = f"""Analyze this research query and determine its domain.

Query: {query}

Domains:
- medical: Healthcare, clinical, patient care, treatments, diseases
- competitive_intelligence: Business, companies, markets, competitors
- regulatory: Laws, regulations, compliance, certifications
- academic: Scientific research, theoretical studies
- general: Doesn't fit other categories

Respond with:
DOMAIN: [domain name]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]
"""
        
        response = await llm_router.complete(
            messages=[{"role": "user", "content": prompt}],
            model="local-fast"
        )
        
        # Parse response
        domain, confidence, reasoning = self._parse_llm_response(response)
        return domain, confidence, reasoning
```

### 2.2 Hybrid Detection

```python
async def detect_domain(
    self,
    query: str,
    llm_router=None
) -> tuple[str, float, str]:
    """
    Hybrid domain detection.
    
    1. Try keyword-based first
    2. If confidence < 0.3, use LLM
    3. Return best result
    """
    domain, confidence = self.detect(query)
    
    if confidence >= 0.3:
        return domain, confidence, f"Detected via keyword matching ({confidence:.0%} confidence)"
    
    if llm_router:
        return await self.detect_with_llm(query, llm_router)
    
    return domain, confidence, "Low confidence keyword detection, LLM not available"
```

---

## 3. AUTO-CONFIGURATION

### 3.1 Configuration Loading

**File**: `/backend/src/research_tool/services/config_loader.py`

```python
import json
from pathlib import Path
from research_tool.models.domain import DomainConfiguration


class ConfigLoader:
    """Load and merge domain configurations."""
    
    def __init__(self, config_dir: str = "./data/domain_configs"):
        self.config_dir = Path(config_dir)
    
    def load_base_config(self, domain: str) -> DomainConfiguration:
        """Load base configuration from JSON file."""
        config_file = self.config_dir / f"{domain}.json"
        
        if not config_file.exists():
            return DomainConfiguration.default()
        
        with open(config_file) as f:
            data = json.load(f)
        
        return DomainConfiguration(**data)
    
    async def load_with_overrides(
        self,
        domain: str,
        memory
    ) -> DomainConfiguration:
        """
        Load base config and apply learned overrides.
        
        Merges:
        1. Base config from JSON
        2. Learned overrides from SQLite
        """
        base = self.load_base_config(domain)
        
        # Get learned overrides
        overrides = await memory.get_domain_overrides(domain)
        
        if overrides:
            # Merge preferred sources (learned first)
            if overrides.get("preferred_sources"):
                learned = overrides["preferred_sources"]
                base.primary_sources = learned + [
                    s for s in base.primary_sources if s not in learned
                ]
            
            # Exclude learned exclusions
            if overrides.get("excluded_sources"):
                base.excluded_sources.extend(overrides["excluded_sources"])
        
        return base
```

### 3.2 Domain Config Files

**File**: `/backend/data/domain_configs/medical.json`

```json
{
    "domain": "medical",
    "primary_sources": ["pubmed", "semantic_scholar"],
    "secondary_sources": ["arxiv", "unpaywall"],
    "academic_required": true,
    "verification_threshold": 0.8,
    "keywords": ["clinical", "patient", "treatment", "diagnosis"],
    "excluded_sources": ["wikipedia", "reddit"]
}
```

**File**: `/backend/data/domain_configs/competitive_intelligence.json`

```json
{
    "domain": "competitive_intelligence",
    "primary_sources": ["tavily", "exa", "brave"],
    "secondary_sources": ["news_api"],
    "academic_required": false,
    "verification_threshold": 0.6,
    "keywords": ["company", "market", "competitor", "funding"],
    "excluded_sources": []
}
```

---

## 4. CROSS-VERIFICATION

### 4.1 Fact Verification

**File**: `/backend/src/research_tool/agent/nodes/verify.py`

```python
from typing import Optional
from research_tool.models.entities import Fact


class FactVerifier:
    """Cross-verify facts across sources."""
    
    async def verify_facts(
        self,
        facts: list[Fact],
        llm_router
    ) -> list[Fact]:
        """
        Verify facts by comparing across sources.
        
        Rules:
        - 1 source: confidence = 0.3
        - 2 sources agreeing: confidence = 0.6
        - 3+ sources agreeing: confidence = 0.85
        - Contradiction found: confidence = 0.2, flag for review
        """
        verified_facts = []
        
        for fact in facts:
            # Group facts by semantic similarity
            similar_facts = self._find_similar_facts(fact, facts)
            
            if len(similar_facts) == 0:
                # Single source
                fact.confidence = 0.3
                fact.verified = False
            else:
                # Check for agreement or contradiction
                agreements, contradictions = self._analyze_claims(
                    fact, similar_facts, llm_router
                )
                
                if contradictions:
                    fact.confidence = 0.2
                    fact.verified = False
                    fact.contradictions = [c.statement for c in contradictions]
                elif len(agreements) >= 2:
                    fact.confidence = 0.85
                    fact.verified = True
                else:
                    fact.confidence = 0.6
                    fact.verified = True
            
            verified_facts.append(fact)
        
        return verified_facts
    
    async def _analyze_claims(
        self,
        fact: Fact,
        similar_facts: list[Fact],
        llm_router
    ) -> tuple[list[Fact], list[Fact]]:
        """Use LLM to detect agreement vs contradiction."""
        
        prompt = f"""Compare these statements and determine if they agree or contradict.

Main statement: {fact.statement}

Comparison statements:
{chr(10).join(f"- {f.statement}" for f in similar_facts)}

For each comparison, respond:
AGREES or CONTRADICTS

Be precise: different numbers, dates, or claims = CONTRADICTS
"""
        
        response = await llm_router.complete(
            messages=[{"role": "user", "content": prompt}],
            model="local-fast"
        )
        
        # Parse response and classify
        agreements = []
        contradictions = []
        # ... parsing logic ...
        
        return agreements, contradictions
```

### 4.2 Contradiction Detection

```python
def detect_contradictions(
    self,
    facts: list[Fact]
) -> list[tuple[Fact, Fact, str]]:
    """
    Find contradicting facts.
    
    Returns: list of (fact1, fact2, reason)
    """
    contradictions = []
    
    for i, fact1 in enumerate(facts):
        for fact2 in facts[i+1:]:
            if self._are_related(fact1, fact2):
                if self._contradict(fact1, fact2):
                    contradictions.append((
                        fact1,
                        fact2,
                        f"Conflicting claims: '{fact1.statement}' vs '{fact2.statement}'"
                    ))
    
    return contradictions
```

---

## 5. CONFIDENCE SCORING

### 5.1 Composite Score

**File**: `/backend/src/research_tool/agent/decisions/confidence.py`

```python
from dataclasses import dataclass


@dataclass
class ConfidenceScore:
    """Composite confidence score."""
    overall: float
    source_quality: float
    verification_status: float
    citation_support: float
    reasoning: str


class ConfidenceCalculator:
    """Calculate confidence scores for facts and claims."""
    
    def calculate(
        self,
        fact,
        source_scores: dict[str, float],
        is_verified: bool,
        citation_count: int
    ) -> ConfidenceScore:
        """
        Calculate composite confidence.
        
        Components:
        - source_quality: Average quality of sources (40%)
        - verification_status: Cross-verified or not (40%)
        - citation_support: Number of citations (20%)
        """
        # Source quality (average of source effectiveness scores)
        sources = fact.sources
        if sources:
            source_quality = sum(source_scores.get(s, 0.5) for s in sources) / len(sources)
        else:
            source_quality = 0.3
        
        # Verification status
        verification_status = 0.9 if is_verified else 0.4
        
        # Citation support (logarithmic scale)
        import math
        citation_support = min(1.0, math.log(citation_count + 1) / 5)
        
        # Weighted composite
        overall = (
            0.4 * source_quality +
            0.4 * verification_status +
            0.2 * citation_support
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            source_quality, verification_status, citation_support, overall
        )
        
        return ConfidenceScore(
            overall=overall,
            source_quality=source_quality,
            verification_status=verification_status,
            citation_support=citation_support,
            reasoning=reasoning
        )
    
    def _generate_reasoning(
        self,
        source_quality: float,
        verification_status: float,
        citation_support: float,
        overall: float
    ) -> str:
        """Generate human-readable confidence explanation."""
        parts = []
        
        if source_quality > 0.7:
            parts.append("from high-quality sources")
        elif source_quality < 0.4:
            parts.append("from lower-quality sources")
        
        if verification_status > 0.8:
            parts.append("verified across multiple sources")
        else:
            parts.append("not independently verified")
        
        if citation_support > 0.6:
            parts.append("well-cited in literature")
        
        confidence_level = "high" if overall > 0.7 else "moderate" if overall > 0.4 else "low"
        
        return f"{confidence_level.title()} confidence: {', '.join(parts)}"
```

---

## 6. LEARNING UPDATES

### 6.1 Post-Research Learning

**File**: `/backend/src/research_tool/agent/nodes/learn.py`

```python
from research_tool.core import get_logger

logger = get_logger(__name__)


async def update_learning(
    state,
    memory
) -> None:
    """
    Update learned knowledge after research.
    
    Updates:
    1. Source effectiveness scores
    2. Domain configuration overrides
    3. Access failure records
    """
    domain = state.get("domain", "general")
    
    # 1. Update source effectiveness
    for source_result in state.get("all_sources", []):
        await memory.update_source_effectiveness(
            source_name=source_result.source_name,
            domain=domain,
            success=source_result.success,
            quality_score=source_result.quality_score
        )
        logger.info(
            "source_effectiveness_updated",
            source=source_result.source_name,
            domain=domain,
            quality=source_result.quality_score
        )
    
    # 2. Update domain config if new good sources found
    high_quality_sources = [
        s.source_name for s in state.get("all_sources", [])
        if s.quality_score > 0.8 and s.success
    ]
    
    if high_quality_sources:
        await memory.update_domain_preferred_sources(
            domain=domain,
            sources=high_quality_sources
        )
        logger.info(
            "domain_config_updated",
            domain=domain,
            preferred_sources=high_quality_sources
        )
    
    # 3. Record access failures (already done in obstacle handler)
    # Just log summary
    failures = state.get("access_failures", [])
    if failures:
        logger.info(
            "access_failures_recorded",
            count=len(failures),
            sources=list(set(f.source_name for f in failures))
        )
```

### 6.2 Learning Verification

```python
async def verify_learning_applied(
    query: str,
    domain: str,
    memory
) -> dict:
    """
    Verify that past learning influences current research.
    
    Returns dict showing how memory was used.
    """
    # Check if past research found
    past_research = await memory.search_similar(query, limit=5)
    
    # Check if source rankings were used
    source_scores = await memory.get_ranked_sources(domain)
    
    # Check if known failures were avoided
    known_failures = await memory.get_failed_urls()
    
    return {
        "past_research_found": len(past_research),
        "source_rankings_available": len(source_scores),
        "known_failures_avoided": len(known_failures),
        "learning_applied": len(past_research) > 0 or len(source_scores) > 0
    }
```

---

## 7. ENHANCED PRIVACY RECOMMENDATION

### 7.1 NLP-Based Detection

**File**: `/backend/src/research_tool/services/llm/selector.py` (enhanced)

```python
async def recommend_privacy_mode_enhanced(
    self,
    query: str,
    attachments: list[str] = None,
    llm_router = None
) -> tuple[PrivacyMode, str]:
    """
    Enhanced privacy recommendation with NLP.
    
    Analyzes:
    1. Query text for sensitive keywords
    2. Attached documents (if any)
    3. LLM assessment of sensitivity
    """
    # Basic keyword check
    sensitive_keywords = [
        "confidential", "private", "internal", "secret",
        "proprietary", "nda", "personal", "medical", "financial",
        "patient", "employee", "salary", "ssn", "password"
    ]
    
    query_lower = query.lower()
    found_keywords = [kw for kw in sensitive_keywords if kw in query_lower]
    
    # If clear keywords found, recommend local
    if found_keywords:
        return (
            PrivacyMode.LOCAL_ONLY,
            f"Detected sensitive content: {', '.join(found_keywords)}. "
            "Recommending local-only processing to protect data privacy."
        )
    
    # If attachments, assume potentially sensitive
    if attachments:
        return (
            PrivacyMode.LOCAL_ONLY,
            "Documents attached. Recommending local-only processing "
            "as document contents may be sensitive."
        )
    
    # Use LLM for nuanced assessment if available
    if llm_router:
        assessment = await self._llm_sensitivity_assessment(query, llm_router)
        if assessment["is_sensitive"]:
            return (
                PrivacyMode.LOCAL_ONLY,
                f"AI assessment: {assessment['reasoning']}"
            )
    
    # Default: cloud allowed
    return (
        PrivacyMode.CLOUD_ALLOWED,
        "No sensitive content detected. Cloud processing enabled for optimal results."
    )

async def _llm_sensitivity_assessment(
    self,
    query: str,
    llm_router
) -> dict:
    """Use LLM to assess query sensitivity."""
    prompt = f"""Assess if this query involves sensitive information that should be processed locally.

Query: {query}

Sensitive content includes:
- Personal identifiable information (PII)
- Medical/health information
- Financial data
- Company confidential information
- Legal matters
- Anything that could harm someone if leaked

Respond with:
IS_SENSITIVE: true/false
REASONING: [brief explanation]
"""
    
    response = await llm_router.complete(
        messages=[{"role": "user", "content": prompt}],
        model="local-fast"  # Always use local for this assessment!
    )
    
    # Parse response
    is_sensitive = "true" in response.lower().split("is_sensitive")[1][:20].lower()
    reasoning = response.split("REASONING:")[1].strip() if "REASONING:" in response else ""
    
    return {"is_sensitive": is_sensitive, "reasoning": reasoning}
```

---

## 8. TESTS

### 8.1 Domain Detection Tests

```python
def test_medical_domain_detected():
    """Medical keywords trigger medical domain."""
    detector = DomainDetector()
    domain, confidence = detector.detect("What are the latest treatments for diabetes patients?")
    assert domain == "medical"
    assert confidence > 0.2

def test_ci_domain_detected():
    """Business keywords trigger CI domain."""
    detector = DomainDetector()
    domain, confidence = detector.detect("Who are OpenAI's main competitors and their funding?")
    assert domain == "competitive_intelligence"

def test_unknown_domain_returns_general():
    """Ambiguous queries return general domain."""
    detector = DomainDetector()
    domain, confidence = detector.detect("What is the meaning of life?")
    assert domain == "general"
```

### 8.2 Cross-Verification Tests

```python
async def test_contradiction_detected():
    """Contradicting facts are flagged."""
    verifier = FactVerifier()
    
    facts = [
        Fact(statement="Company A was founded in 2010", sources=["source1"]),
        Fact(statement="Company A was founded in 2015", sources=["source2"])
    ]
    
    verified = await verifier.verify_facts(facts, mock_llm)
    
    assert any(f.contradictions for f in verified)

async def test_agreement_increases_confidence():
    """Multiple agreeing sources increase confidence."""
    # Test implementation
```

### 8.3 Learning Tests

```python
async def test_learning_influences_future_research():
    """Past research affects future planning."""
    memory = MockMemory()
    
    # First research
    await update_learning(research_state_1, memory)
    
    # Check learning applied
    result = await verify_learning_applied("similar query", "medical", memory)
    assert result["learning_applied"]
```

---

## 9. VALIDATION GATE

```
□ Domain detection >90% accuracy on test set
□ Auto-configuration loads correct settings
□ Cross-verification catches planted contradictions
□ Confidence scores correlate with actual quality
□ Learning persists to next research
□ Past research influences future planning (verified)
□ Privacy recommendations accurate
□ Recommendations include clear reasoning
```

---

## 10. COMMIT AND MERGE

```bash
git add .
git commit -m "feat: complete phase 5 intelligence features [BUILD-PLAN Phase 5]"
git checkout develop
git merge phase-5-intelligence
git push origin develop
```

---

*END OF PHASE 5 GUIDE*
