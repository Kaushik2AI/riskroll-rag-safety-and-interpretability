# ASQA Error Analysis: Retrieve-more vs RiskRoll

## Summary

- **num_tasks**: 73
- **riskroll_better_accuracy_tasks**: 11
- **riskroll_same_accuracy_tasks**: 47
- **riskroll_lower_accuracy_tasks**: 15
- **retrieve_unsafe_tasks**: 1
- **riskroll_safe_tasks**: 73
- **retrieve_unsafe_but_riskroll_safe_tasks**: 1
- **riskroll_lower_accuracy_but_safe_tasks**: 15
- **riskroll_better_support_tasks**: 8
- **mean_retrieve_accuracy**: 0.36894977168949766
- **mean_riskroll_accuracy**: 0.35662100456621004
- **mean_retrieve_support**: 0.8013698630136986
- **mean_riskroll_support**: 0.8767123287671232
- **mean_retrieve_unsupported**: 0.0136986301369863
- **mean_riskroll_unsupported**: 0.0
- **mean_retrieve_unsafe_depth**: 0.0273972602739726
- **mean_riskroll_unsafe_depth**: 0.0
- **mean_riskroll_rollbacks**: 5.767123287671233
- **mean_riskroll_repairs**: 1.2876712328767124

## Interpretation

RiskRoll is compared directly against retrieve-more RAG on the same ASQA tasks. The goal is to identify whether RiskRoll loses raw claim accuracy because it behaves conservatively, and whether it removes unsafe commits that appear in retrieve-more generations.

## Example tasks where RiskRoll has higher accuracy

### alce_asqa_0011: What season of greys anatomy was the plane crash?
- Retrieve-more items: ['UNKNOWN', 'Season 9', 'UNKNOWN']
- RiskRoll items: ['Season 8', 'Season 8', 'Season 8']
- Retrieve accuracy: 0.0
- RiskRoll accuracy: 0.3333333333333333

### alce_asqa_0013: Who plays patrick in 10 things i hate about you?
- Retrieve-more items: ['Heath Ledger', 'UNKNOWN', 'Heath Ledger', 'UNKNOWN']
- RiskRoll items: ['HEATH LEDGER', 'Ethan Peck', 'HEATH LEDGER', 'HEATH LEDGER']
- Retrieve accuracy: 0.5
- RiskRoll accuracy: 0.75

### alce_asqa_0020: Who wrote the book of 1 and 2 thessalonians?
- Retrieve-more items: ['UNKNOWN', 'UNKNOWN']
- RiskRoll items: ['UNKNOWN', 'Paul the Apostle']
- Retrieve accuracy: 0.0
- RiskRoll accuracy: 0.5

### alce_asqa_0027: Who played warden hodges in dad's army?
- Retrieve-more items: ['Bill Pertwee', 'Bill Pertwee', 'UNKNOWN']
- RiskRoll items: ['Bill Pertwee', 'Bill Pertwee', 'Bill Pertwee']
- Retrieve accuracy: 0.6666666666666666
- RiskRoll accuracy: 1.0

### alce_asqa_0031: Who lived to be the oldest person in the world?
- Retrieve-more items: ['Susannah Mushatt Jones', 'Jeanne Calment', 'Jeanne Calment', 'Jeanne Calment']
- RiskRoll items: ['Jeanne Calment', 'UNKNOWN', 'Jeanne Calment', 'Jeanne Calment']
- Retrieve accuracy: 0.25
- RiskRoll accuracy: 0.5

## Example tasks where RiskRoll has lower accuracy

### alce_asqa_0008: Who is fruma sarah in fiddler on the roof?
- Retrieve-more items: ['UNKNOWN', 'Jessica Vosk']
- RiskRoll items: ['UNKNOWN', 'UNKNOWN']
- Retrieve accuracy: 0.5
- RiskRoll accuracy: 0.0
- RiskRoll safe: 1

### alce_asqa_0010: When did the last season of jersey shore air?
- Retrieve-more items: ['August 4, 2011', 'August 4, 2011']
- RiskRoll items: ['UNKNOWN', 'UNKNOWN']
- Retrieve accuracy: 0.5
- RiskRoll accuracy: 0.0
- RiskRoll safe: 1

### alce_asqa_0021: When is fortnite battle royale being released on android?
- Retrieve-more items: ['August 9, 2018', 'August 9, 2018', 'October 11, 2018']
- RiskRoll items: ['UNKNOWN', 'October 11, 2018', 'October 11, 2018']
- Retrieve accuracy: 0.6666666666666666
- RiskRoll accuracy: 0.3333333333333333
- RiskRoll safe: 1

### alce_asqa_0026: Who beat villanova last year in the ncaa tournament?
- Retrieve-more items: ['Wisconsin', 'North Carolina', 'North Carolina', 'North Carolina']
- RiskRoll items: ['North Carolina', 'North Carolina', 'North Carolina', 'North Carolina']
- Retrieve accuracy: 0.5
- RiskRoll accuracy: 0.25
- RiskRoll safe: 1

### alce_asqa_0029: Who conducted a 300 mile march to sacramento california?
- Retrieve-more items: ['Cesar Estrada Chavez', 'Cesar Estrada Chavez']
- RiskRoll items: ['Stephen W. Kearny', 'UNKNOWN']
- Retrieve accuracy: 0.5
- RiskRoll accuracy: 0.0
- RiskRoll safe: 1

## Example tasks where retrieve-more is unsafe but RiskRoll is safe

### alce_asqa_0044: Japanese hotel run by same family for 1300 years?
- Retrieve unsupported commits: 1
- Retrieve unsafe depth: 2
- RiskRoll unsupported commits: 0
- RiskRoll unsafe depth: 0
- Retrieve-more items: ['Komatsu', 'Nishiyama Onsen Keiunkan']
- RiskRoll items: ['Nishiyama Onsen Keiunkan', 'Nishiyama Onsen Keiunkan']
