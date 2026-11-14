# Experiment 5B Failure Diagnostics

## Summary

- **run_name**: experiment5b_chartqa_qwen_vlm_10
- **n**: 10
- **top_k**: 6
- **standard_claim_accuracy**: 0.4
- **standard_evidence_accuracy**: 0
- **standard_grounded_claim_rate**: 0
- **standard_wrong_evidence_count**: 10
- **standard_unsafe_prefix_depth**: 9
- **standard_downstream_contamination**: 9
- **riskroll_claim_accuracy**: 0.7
- **riskroll_evidence_accuracy**: 0.3
- **riskroll_grounded_claim_rate**: 0.3
- **riskroll_wrong_evidence_count**: 7
- **riskroll_unsafe_prefix_depth**: 7
- **riskroll_downstream_contamination**: 7
- **riskroll_rollback_count**: 13
- **riskroll_repair_count**: 5
- **riskroll_abstention_count**: 0
- **verifier_false_accepts**: 7
- **verifier_false_rejects_or_abstentions**: 0

## Main issue

RiskRoll improves answer accuracy over Standard RAG, but the Qwen verifier false-accepts wrong chart evidence. This causes low evidence accuracy and low grounded rate.

## Row-level outcomes

| Step | Gold rank | Standard grounded | RiskRoll grounded | RiskRoll rank | Action | Question | Gold | RiskRoll pred |
|---:|---:|---:|---:|---:|---|---|---|---|
| 1 | 2 | False | True | 2 | repair_and_accept_claim | Is the value of Favorable 38 in 2015? | Yes | Yes |
| 2 | 4 | False | True | 4 | repair_and_accept_claim | How many values are below 40 in Unfavorable graph? | 6 | 6 |
| 3 | 3 | False | False | 2 | repair_and_accept_claim | In which year the value was 51? | 2014 | 2011 |
| 4 | 5 | False | False | 1 | accept_trusted_claim | What is the sum favourable value in the year 2014 and 2015? | 95 | 95 |
| 5 | 4 | False | False | 1 | accept_trusted_claim | In which year the Mexican governments campaign against drugs traffickers is making 47 percent progress? | 2012 | 2012 |
| 6 | 2 | False | False | 1 | accept_trusted_claim | What is the sum of making progress ,losing ground and same in the year 2011? | 99 | 109 |
| 7 | 5 | False | False | 1 | accept_trusted_claim | How many intercepting point(s) is/are there? | 1 | 1 |
| 8 | 6 | False | True | 6 | repair_and_accept_claim | Which year has the most divergent opinions about Brazil's economy? | 2015 | 2015 |
| 9 | 5 | False | False | 1 | accept_trusted_claim | Which line contains smaller values across all years? | Unfavorable | Unfavorable |
| 10 | 6 | False | False | 4 | repair_and_accept_claim | Deduct the most unfavorable view from the most favorable view? | 49 | 46 |

## Verifier false accepts

Total false accepts: 7

### False accept 1

- Step: 3
- Question: In which year the value was 51?
- Gold answer: 2014
- Predicted answer: 2011
- Gold evidence: chartqa_unique_00002
- Accepted evidence: chartqa_unique_00096
- Candidate rank: 2
- Verifier output: `TRUST`

### False accept 2

- Step: 4
- Question: What is the sum favourable value in the year 2014 and 2015?
- Gold answer: 95
- Predicted answer: 95
- Gold evidence: chartqa_unique_00003
- Accepted evidence: chartqa_unique_00144
- Candidate rank: 1
- Verifier output: `TRUST`

### False accept 3

- Step: 5
- Question: In which year the Mexican governments campaign against drugs traffickers is making 47 percent progress?
- Gold answer: 2012
- Predicted answer: 2012
- Gold evidence: chartqa_unique_00004
- Accepted evidence: chartqa_unique_00005
- Candidate rank: 1
- Verifier output: `TRUST`

### False accept 4

- Step: 6
- Question: What is the sum of making progress ,losing ground and same in the year 2011?
- Gold answer: 99
- Predicted answer: 109
- Gold evidence: chartqa_unique_00005
- Accepted evidence: chartqa_unique_00004
- Candidate rank: 1
- Verifier output: `TRUST`

### False accept 5

- Step: 7
- Question: How many intercepting point(s) is/are there?
- Gold answer: 1
- Predicted answer: 1
- Gold evidence: chartqa_unique_00006
- Accepted evidence: chartqa_unique_00182
- Candidate rank: 1
- Verifier output: `TRUST`

### False accept 6

- Step: 9
- Question: Which line contains smaller values across all years?
- Gold answer: Unfavorable
- Predicted answer: Unfavorable
- Gold evidence: chartqa_unique_00008
- Accepted evidence: chartqa_unique_00097
- Candidate rank: 1
- Verifier output: `TRUST`

### False accept 7

- Step: 10
- Question: Deduct the most unfavorable view from the most favorable view?
- Gold answer: 49
- Predicted answer: 46
- Gold evidence: chartqa_unique_00009
- Accepted evidence: chartqa_unique_00154
- Candidate rank: 4
- Verifier output: `TRUST`
