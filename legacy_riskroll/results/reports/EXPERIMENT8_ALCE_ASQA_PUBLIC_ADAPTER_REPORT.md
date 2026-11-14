# Experiment 8: ALCE-ASQA Public Adapter

ASQA examples are converted into claim-level tasks using qa_pairs.
Each qa_pair becomes a claim/subquestion with short-answer aliases.

## Stats

- **input_path**: /projectnb/medaihack/team4/kaushik_work/riskroll-aaai27-text/external/ALCE/data/asqa_eval_gtr_top100.json
- **records_read**: 100
- **tasks_built**: 73
- **total_claims**: 222
- **mean_claims_per_task**: 3.041095890410959
- **docs_top_k**: 20
- **max_claims_per_task**: 5
- **require_support_in_top100**: True
- **skipped_no_docs**: 0
- **skipped_too_few_claims**: 27
- **skipped_no_supported_claims**: 8
- **mean_first_support_rank**: 6.91701244813278
- **top1_support_rate**: 0.43983402489626555
- **top5_support_rate**: 0.6929460580912863
- **top20_support_rate**: 0.91701244813278

## First task example
**Question:** Who is the original artist of sound of silence?
**Gold long answer:** There are several songs with the title "Sound of Silence". Sounds of Silence is the second studio album by Simon & Garfunkel, released on January 17, 1966. The album's title is a slight modification of the title of the duo's first major hit, "The Sound of Silence", which was recorded in March 1964 and originally was released as "The Sounds of Silence". Another "Sound of Silence" is a song performed by Australian recording artist Dami Im, and is best known as Australia's entry at the Eurovision Song Contest 2016.

- **Subquestion:** Who is the original artist of sound of silence, the song, released in 1964?
  - Gold aliases: ['Simon & Garfunkel', 'Paul Simon and Art Garfunkel', 'Art Garfunkel', 'Paul Simon']
  - First support rank: 1
- **Subquestion:** Who is the original artist of sound of silence, the album?
  - Gold aliases: ['Simon & Garfunkel', 'Paul Simon and Art Garfunkel', 'Art Garfunkel', 'Paul Simon']
  - First support rank: 1
- **Subquestion:** Who is the original artist of sound of silence, the song, released in 2016?
  - Gold aliases: ['Dami Im']
  - First support rank: 10