# Real Dataset Evaluation
- Dataset size: 93733
- Unique resumes: 643
- Unique JDs: 351
- Label distribution: {'HIGH': 1030, 'MEDIUM': 2544, 'LOW': 10354}
- Train / validation / test records: 65419 / 14386 / 13928
- Split: group-aware by resume, seed 42; original source split was not used for evaluation.
- Model: RandomForestClassifier(class_weight='balanced', random_state=42)
- Features: required_skill_match_ratio, preferred_skill_match_ratio, required_skill_matched_count, required_skill_missing_count, preferred_skill_matched_count, candidate_experience_years, required_experience_years, experience_gap, experience_match_ratio, education_level_match, project_relevance, tfidf_similarity, semantic_similarity

## Test metrics
- accuracy: 0.712809
- precision_macro: 0.542241
- recall_macro: 0.614793
- f1_macro: 0.564479
- precision_weighted: 0.770221
- recall_weighted: 0.712809
- f1_weighted: 0.734429
- majority_baseline_accuracy: 0.743395

Model accuracy should be compared with the majority-class baseline because the dataset is imbalanced.

## Confusion matrix (HIGH, MEDIUM, LOW)
```text
[593, 326, 111]
[612, 1238, 694]
[540, 1717, 8097]
```

## Limitations
- Dataset contains generated and synthetic records and is not an independently human-labelled benchmark.
- Evaluation is grouped by resume, but repeated JD text can occur across splits.
- Semantic model was unavailable and was not used.
- Do not use these results to justify automated hiring decisions.
