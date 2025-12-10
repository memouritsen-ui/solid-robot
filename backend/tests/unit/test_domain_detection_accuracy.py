"""Tests for domain detection accuracy.

Task #232: Test: Domain detection accuracy >90%

This test uses a corpus of queries with known expected domains
and verifies the detection accuracy exceeds 90%.
"""

from research_tool.agent.decisions.domain_detector import detect_domain

# Test corpus: (query, expected_domain)
# These queries are designed to be unambiguous representatives of each domain
DOMAIN_TEST_CORPUS: list[tuple[str, str]] = [
    # === MEDICAL DOMAIN (20 queries) ===
    ("What are the symptoms of type 2 diabetes?", "medical"),
    ("Treatment options for chronic heart disease", "medical"),
    ("Clinical trials for cancer therapy", "medical"),
    ("Patient outcomes after knee surgery", "medical"),
    ("Drug interactions with blood pressure medication", "medical"),
    ("Diagnosis criteria for depression disorder", "medical"),
    ("Hospital readmission rates for pneumonia", "medical"),
    ("Medical history of autoimmune diseases", "medical"),
    ("Pharmaceutical treatments for arthritis", "medical"),
    ("Healthcare protocols for infectious disease", "medical"),
    ("Symptoms and diagnosis of Parkinson's disease", "medical"),
    ("Treatment guidelines for asthma patients", "medical"),
    ("Clinical pathology of liver disease", "medical"),
    ("Oncology treatment for breast cancer", "medical"),
    ("Cardiology interventions for heart failure", "medical"),
    ("Patient care for diabetic foot syndrome", "medical"),
    ("Medical therapy for chronic pain management", "medical"),
    ("Disease progression in multiple sclerosis", "medical"),
    ("Drug efficacy for viral infections", "medical"),
    ("Healthcare outcomes for elderly patients", "medical"),

    # === COMPETITIVE INTELLIGENCE DOMAIN (20 queries) ===
    ("What is Apple's market share in smartphones?", "competitive_intelligence"),
    ("Revenue growth of Tesla competitors", "competitive_intelligence"),
    ("Startup funding trends in fintech sector", "competitive_intelligence"),
    ("Company valuation of major tech firms", "competitive_intelligence"),
    ("Product launch strategy of Samsung", "competitive_intelligence"),
    ("Business acquisition targets in retail industry", "competitive_intelligence"),
    ("Competitor analysis for cloud services market", "competitive_intelligence"),
    ("Investment trends in renewable energy companies", "competitive_intelligence"),
    ("Stock performance of pharmaceutical corporations", "competitive_intelligence"),
    ("Enterprise software market competition", "competitive_intelligence"),
    ("Sales growth of e-commerce companies", "competitive_intelligence"),
    ("Market positioning of luxury brands", "competitive_intelligence"),
    ("Funding rounds for AI startups", "competitive_intelligence"),
    ("Revenue comparison of streaming services", "competitive_intelligence"),
    ("Company profit margins in automotive industry", "competitive_intelligence"),
    ("Business strategy of retail competitors", "competitive_intelligence"),
    ("Market trends in semiconductor industry", "competitive_intelligence"),
    ("Shareholder value of tech companies", "competitive_intelligence"),
    ("Industry analysis for electric vehicles", "competitive_intelligence"),
    ("Corporation expansion plans in Asia market", "competitive_intelligence"),

    # === ACADEMIC DOMAIN (20 queries) ===
    ("Peer-reviewed research on climate change", "academic"),
    ("Journal publications on quantum computing", "academic"),
    ("Study methodology for social science research", "academic"),
    ("Citation analysis of influential papers", "academic"),
    ("Academic thesis on machine learning algorithms", "academic"),
    ("Research hypothesis testing methods", "academic"),
    ("University publication on neuroscience", "academic"),
    ("Scholar contributions to economic theory", "academic"),
    ("Dissertation research on renewable energy", "academic"),
    ("Peer-reviewed study on cognitive psychology", "academic"),
    ("Academic journal on materials science", "academic"),
    ("Research paper methodology in biology", "academic"),
    ("Publication citation metrics analysis", "academic"),
    ("University research on nanotechnology", "academic"),
    ("Scholar work on linguistic theory", "academic"),
    ("Academic study of historical events", "academic"),
    ("Research methodology in sociology", "academic"),
    ("Journal article on environmental science", "academic"),
    ("Thesis research on computer networks", "academic"),
    ("Academic analysis of political theory", "academic"),

    # === REGULATORY DOMAIN (20 queries) ===
    ("FDA approval requirements for medical devices", "regulatory"),
    ("Compliance standards for pharmaceutical industry", "regulatory"),
    ("Government regulations on data privacy", "regulatory"),
    ("Legal requirements for financial reporting", "regulatory"),
    ("Policy guidelines for environmental protection", "regulatory"),
    ("Regulatory mandate for food safety", "regulatory"),
    ("Compliance audit requirements for banks", "regulatory"),
    ("FDA guidelines for clinical trials", "regulatory"),
    ("Legal legislation on consumer protection", "regulatory"),
    ("Government authority oversight of telecoms", "regulatory"),
    ("License requirements for medical practitioners", "regulatory"),
    ("Permit regulations for construction projects", "regulatory"),
    ("Regulatory approval process for new drugs", "regulatory"),
    ("Compliance requirements for GDPR", "regulatory"),
    ("Legal standards for workplace safety", "regulatory"),
    ("Government policy on immigration", "regulatory"),
    ("Regulatory rules for securities trading", "regulatory"),
    ("FDA compliance for food additives", "regulatory"),
    ("Legal mandate for environmental audits", "regulatory"),
    ("Policy requirements for aviation safety", "regulatory"),

    # === GENERAL DOMAIN (20 queries) ===
    ("What is the weather like today?", "general"),
    ("How to cook spaghetti bolognese?", "general"),
    ("Best vacation destinations in Europe", "general"),
    ("How does the moon affect tides?", "general"),
    ("History of the Roman Empire", "general"),
    ("How to learn a new language?", "general"),
    ("Best hiking trails in Colorado", "general"),
    ("Recipe for chocolate chip cookies", "general"),
    ("How do airplanes fly?", "general"),
    ("Famous paintings in the Louvre", "general"),
    ("How to play chess?", "general"),
    ("Best books of 2024", "general"),
    ("How to train a puppy?", "general"),
    ("What causes rainbows?", "general"),
    ("Famous landmarks in Paris", "general"),
    ("How to fix a leaky faucet?", "general"),
    ("Best podcasts about history", "general"),
    ("How does photosynthesis work?", "general"),
    ("Tips for better sleep", "general"),
    ("How to start a garden?", "general"),
]


class TestDomainDetectionAccuracy:
    """Tests for domain detection accuracy metrics."""

    def test_domain_detection_accuracy_exceeds_90_percent(self) -> None:
        """Verify domain detection accuracy exceeds 90% on test corpus.

        This is the primary accuracy test per Task #232.
        """
        correct = 0
        total = len(DOMAIN_TEST_CORPUS)
        failures: list[tuple[str, str, str]] = []

        for query, expected_domain in DOMAIN_TEST_CORPUS:
            result = detect_domain(query)

            if result.domain == expected_domain:
                correct += 1
            else:
                failures.append((query, expected_domain, result.domain))

        accuracy = correct / total

        # Show failures for debugging
        if failures:
            failure_details = "\n".join(
                f"  - '{q[:50]}...' expected={exp}, got={got}"
                for q, exp, got in failures[:10]  # Show first 10
            )
            if len(failures) > 10:
                failure_details += f"\n  ... and {len(failures) - 10} more"
        else:
            failure_details = "None"

        assert accuracy >= 0.90, (
            f"Domain detection accuracy {accuracy:.1%} is below 90% threshold.\n"
            f"Correct: {correct}/{total}\n"
            f"Failures:\n{failure_details}"
        )

    def test_medical_domain_accuracy(self) -> None:
        """Verify medical domain detection accuracy."""
        medical_queries = [q for q, d in DOMAIN_TEST_CORPUS if d == "medical"]

        correct = sum(
            1 for q in medical_queries
            if detect_domain(q).domain == "medical"
        )

        accuracy = correct / len(medical_queries)
        assert accuracy >= 0.85, f"Medical accuracy {accuracy:.1%} below 85%"

    def test_competitive_intelligence_domain_accuracy(self) -> None:
        """Verify competitive intelligence domain detection accuracy."""
        ci_queries = [q for q, d in DOMAIN_TEST_CORPUS if d == "competitive_intelligence"]

        correct = sum(
            1 for q in ci_queries
            if detect_domain(q).domain == "competitive_intelligence"
        )

        accuracy = correct / len(ci_queries)
        assert accuracy >= 0.85, f"CI accuracy {accuracy:.1%} below 85%"

    def test_academic_domain_accuracy(self) -> None:
        """Verify academic domain detection accuracy."""
        academic_queries = [q for q, d in DOMAIN_TEST_CORPUS if d == "academic"]

        correct = sum(
            1 for q in academic_queries
            if detect_domain(q).domain == "academic"
        )

        accuracy = correct / len(academic_queries)
        assert accuracy >= 0.85, f"Academic accuracy {accuracy:.1%} below 85%"

    def test_regulatory_domain_accuracy(self) -> None:
        """Verify regulatory domain detection accuracy."""
        regulatory_queries = [q for q, d in DOMAIN_TEST_CORPUS if d == "regulatory"]

        correct = sum(
            1 for q in regulatory_queries
            if detect_domain(q).domain == "regulatory"
        )

        accuracy = correct / len(regulatory_queries)
        assert accuracy >= 0.85, f"Regulatory accuracy {accuracy:.1%} below 85%"

    def test_general_domain_accuracy(self) -> None:
        """Verify general domain detection (no false positives)."""
        general_queries = [q for q, d in DOMAIN_TEST_CORPUS if d == "general"]

        correct = sum(
            1 for q in general_queries
            if detect_domain(q).domain == "general"
        )

        accuracy = correct / len(general_queries)
        # General is harder - keywords may accidentally match
        assert accuracy >= 0.80, f"General accuracy {accuracy:.1%} below 80%"

    def test_confidence_correlates_with_accuracy(self) -> None:
        """Verify higher confidence scores correlate with correct predictions."""
        high_confidence_correct = 0
        high_confidence_total = 0
        low_confidence_correct = 0
        low_confidence_total = 0

        for query, expected_domain in DOMAIN_TEST_CORPUS:
            result = detect_domain(query)
            is_correct = result.domain == expected_domain

            if result.confidence >= 0.5:
                high_confidence_total += 1
                if is_correct:
                    high_confidence_correct += 1
            else:
                low_confidence_total += 1
                if is_correct:
                    low_confidence_correct += 1

        # High confidence predictions should be more accurate
        if high_confidence_total > 0 and low_confidence_total > 0:
            high_acc = high_confidence_correct / high_confidence_total
            low_acc = low_confidence_correct / low_confidence_total

            # High confidence should be at least as accurate as low confidence
            # (ideally better, but at minimum not worse)
            assert high_acc >= low_acc * 0.9, (
                f"High confidence accuracy ({high_acc:.1%}) should be >= "
                f"low confidence accuracy ({low_acc:.1%})"
            )
