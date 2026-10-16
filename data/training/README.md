# Training data and model status

## Dataset in use

The current training pipeline reads the three Parquet files under
`data/training/resume-job-fit-merged-v1/data/` and combines their 93,733
candidate–job records. The original train/test split is not used for evaluation.
The data contains 643 unique resume texts and 351 unique job descriptions.

The Parquet shards are intentionally not committed to the public GitHub
repository because two individual shards exceed GitHub's 100 MB file limit.
Download the dataset from
<https://huggingface.co/datasets/med2425/resume-job-fit-merged-v1> and place
the three Parquet files in `resume-job-fit-merged-v1/data/` before retraining.

The source dataset is a merged collection containing generated and synthetic
examples. Its labels are `Good Fit`, `Potential Fit`, and `No Fit`, mapped by
the project to `HIGH`, `MEDIUM`, and `LOW`. Refer to the dataset's bundled
README for its published source and generation details. These records are not
an independently human-labelled production benchmark.

## Split and model

`backend/training/train_model.py` creates train, validation, and test groups by
resume ID with seed 42. All pairs for one resume stay in one split. The current
saved model is a class-weighted Random Forest with 65,419 training, 14,386
validation, and 13,928 test records. The saved metadata records the split
leakage check and metrics in `backend/models/model_metadata.json`.

## Evaluation status and limitations

See `evaluation_report.md` and `evaluation_report.json` for the full results.
The test macro F1 is 0.5645 and accuracy is 0.7128. The majority-class baseline
has higher accuracy (0.7434), so accuracy alone overstates usefulness on this
imbalanced dataset. The model has not been validated on an independently
collected, human-labelled dataset. Repeated job descriptions can cross resume
groups, and semantic similarity was unavailable during training and was set
to zero. Treat scores as experimental decision support, not automated hiring
decisions.

## Reproduce

From the repository root, run:

```powershell
python backend/training/train_model.py
```

The training process writes the model, metadata, grouped split IDs, and report
artifacts. Review the report and limitations before using a newly trained
model.
