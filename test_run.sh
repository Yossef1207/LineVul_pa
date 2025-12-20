#!/bin/bash
set -euo pipefail

# ins Projektverzeichnis springen (Ordner, in dem dieses Script liegt)
cd "$(dirname "$0")"

# jetzt in den linevul-Ordner (wenn linevul_main.py dort liegt)
cd linevul

python linevul_main.py \
  --output_dir=./saved_models \
  --model_type=roberta \
  --tokenizer_name=microsoft/codebert-base \
  --model_name=model.bin \
  --model_name_or_path=./saved_models/checkpoint-best-f1 \
  --do_test \
  --test_data_file=../data/reposvul_dataset/test.csv \
  --block_size 512 \
  --eval_batch_size 16 \
  --seed 123456 2>&1 \
  --use_non_pretrained_model | tee test_rerun.log \