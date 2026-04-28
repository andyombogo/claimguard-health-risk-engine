# Prototype Screens

The Streamlit prototype is organized into four reviewer-oriented pages. Together, they show how ClaimGuard supports triage, investigation, and workflow tracking without removing human control from the review process.

## 1. Claims Review Queue

**Purpose:** Help a claims officer see the overall portfolio, filter the queue, and identify which claims need attention first.

**Key elements**

- Summary cards for total claims, high-risk claims, critical-risk claims, and total flagged claims
- Filters for risk band, provider, provider type, claim status, and date range
- Queue table with claim amount, score, risk band, number of flags, and recommended action
- Charts showing counts and claim amounts by risk band

**Suggested screenshot placeholder**

`outputs/screenshots/claims_review_queue.png`

## 2. Claim Risk Profile

**Purpose:** Let the reviewer open one claim and understand the reasoning behind its prioritization.

**Key elements**

- Claim summary
- Risk score and risk band
- Recommended action
- Triggered rule list with explanations
- Related claims view where available
- Reviewer note area
- Mock action buttons for reviewed, checker, and escalation steps

**Suggested screenshot placeholder**

`outputs/screenshots/claim_risk_profile.png`

## 3. Provider Intelligence

**Purpose:** Surface provider-level patterns that may warrant context-aware review.

**Key elements**

- Provider table with claim counts, average claim amounts, high-risk claim counts, and percentage flagged
- Charts for top providers by claim volume, high-risk claims, and average claim amount
- Clear note that provider patterns are screening indicators, not conclusions

**Suggested screenshot placeholder**

`outputs/screenshots/provider_intelligence.png`

## 4. Audit Log

**Purpose:** Demonstrate how review actions can be tracked in a maker-checker style workflow.

**Key elements**

- Recent review actions
- Status changes by claim
- Reviewer role and note fields
- Workflow summary for reviewed, checker-ready, and escalated claims

**Suggested screenshot placeholder**

`outputs/screenshots/audit_log.png`

## Demo Guidance

For presentations, a good sequence is:

1. Start with the queue to show the triage problem and prioritization view.
2. Open a single claim profile to show explainability.
3. Move to provider intelligence to show portfolio-level context.
4. Close on the audit log to emphasize governance and traceability.
