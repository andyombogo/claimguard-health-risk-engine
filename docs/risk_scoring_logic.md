# Risk Scoring Logic

ClaimGuard uses a rule-based scoring approach for the MVP. Each review rule contributes a configured number of points when it is triggered, and the total becomes the claim's risk score. The logic is transparent by design so a reviewer can trace a score back to specific review indicators.

## Why Rule-Based Scoring

For an early prototype, rule-based logic is easier to explain, test, and challenge than a black-box model. A claims officer or reviewer can inspect the triggered rules, understand the rationale, and decide whether the recommendation fits the context of the claim.

This is especially important in a claims-review workflow where high scores should trigger closer human review, not automatic accusations.

## Current Rule Families

- Exact duplicate claim
- Near duplicate claim
- Abnormal billing
- Diagnosis-treatment mismatch
- Provider pattern risk
- Missing documents

Each rule has a default point value, severity, and short description in `src/config/risk_rules.yaml`.

## Scoring Method

1. Run all configured rules against the claims data.
2. Keep the flagged rule outputs for each `claim_id`.
3. Sum the points for each claim.
4. Cap the total score at `100`.
5. Assign a risk band based on the capped score.
6. Map the risk band to a recommended action.

## Default Risk Bands

| Score Range | Risk Band | Default Action |
| --- | --- | --- |
| 0-24 | Low Risk | Fast-track standard review |
| 25-49 | Medium Risk | Standard review with attention to flagged items |
| 50-74 | High Risk | Maker-checker review required |
| 75-100 | Critical Risk | Escalate for detailed investigation before approval |

## Explainability

The score is never meant to stand alone. ClaimGuard also returns:

- the triggered rules
- the points contributed by each rule
- the highest observed severity
- a concise human-readable explanation
- a recommended action framed as review guidance

This makes the score auditable and easier to discuss during review, escalation, or QA.

## Limitations

- Rule quality depends on the quality of the input data
- Thresholds may need calibration for different claim mixes
- Provider and duplicate checks are stronger when historical context is available
- Rule-based scoring can miss subtle patterns that a more advanced model might detect
- A high score does not mean fraud is confirmed

## Why The MVP Avoids Black-Box-Only Fraud Prediction

The prototype deliberately avoids leading with opaque prediction because:

- reviewers need to understand why a claim is being prioritized
- unexplained scores are difficult to defend in operational workflows
- false positives can create unnecessary friction or reputational harm
- early-stage innovation work benefits from logic that can be challenged and improved quickly

Future phases may explore anomaly detection or hybrid approaches, but the MVP keeps explainability and reviewer trust as first-order requirements.
