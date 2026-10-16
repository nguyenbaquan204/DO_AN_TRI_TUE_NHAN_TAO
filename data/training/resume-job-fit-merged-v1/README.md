---
dataset_info:
  features:
  - name: resume
    dtype: string
  - name: jd
    dtype: string
  - name: label
    dtype: string
  - name: source
    dtype: string
  - name: resume_domain
    dtype: string
  - name: jd_domain
    dtype: string
  splits:
  - name: train
    num_bytes: 699473455
    num_examples: 80017
  - name: test
    num_bytes: 125960894
    num_examples: 13716
  download_size: 300877211
  dataset_size: 825434349
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: test
    path: data/test-*
language:
- en
---

# Resume-Job Fit Dataset (Merged)

**A high-quality dataset for training models to evaluate how well a resume fits a job description.**

This dataset is designed for **multi-class text classification** (Good Fit / Potential Fit / No Fit).

## Dataset Summary

| Split   | Examples |
|---------|----------|
| **train** | 80,017   |
| **test**  | 13,716   |

**Total: 93,733 examples**

## Features

- **`resume`** (`string`): Complete resume text  
- **`jd`** (`string`): Complete job description text  
- **`label`** (`string`): `Good Fit`, `Potential Fit`, or `No Fit`  
- **`source`** (`string`): Origin of the example (`ds1_original`, `generated_smart`, `synthetic_test`, ...)  
- **`resume_domain`** (`string`): Detected domain of the resume  
- **`jd_domain`** (`string`): Detected domain of the job description  

## Data Generation Process

### Training Set
- Combined two public datasets: `cnamuangtoun/resume-job-description-fit` and `kens1ang/resume-job-fit-augmented`
- Removed exact duplicates using MD5 hashing
- Generated smart cross-domain pairs using domain classification and adjacency rules
- Labeled using **Qwen2.5-32B** (via Ollama, temperature=0) as an expert recruiter

### Test Set
- Created from the original test split to prevent data leakage
- Generated challenging synthetic pairs with the same domain logic
- No text truncation applied
- Independently labeled by **Qwen2.5-32B**

## Label Definitions

- **Good Fit**: Strong match in skills, experience, education, and role requirements.
- **Potential Fit**: Partial match — candidate has potential but clear gaps exist.
- **No Fit**: Significant mismatch in key requirements.

## Domains Covered
`software`, `data`, `ai`, `finance`, `marketing`, `healthcare`, `management`, `sales`, `design`, `hr`, `legal`, `engineering`, `other`

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("med2425/resume-job-fit-merged-v1")

train = dataset["train"]
test = dataset["test"]

print(train[0])
```

## Citation
```bibtex
@misc{resume-job-fit-merged-v1,
  title = {Resume-Job Fit Dataset},
  author = {Mohamed Douali},                   
  year = {2026},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/datasets/med2425/resume-job-fit-merged-v1}}
}