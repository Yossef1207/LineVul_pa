#!/bin/bash

llms=(codellama gpt-4o)

cd linevul

echo ">>> Testing with ReposVul only"

python linevul_main.py \
    --model_name=model.bin \
    --output_dir=./saved_models \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --do_test \
    --do_sorting_by_line_scores \
    --effort_at_top_k=0.2 \
    --top_k_recall_by_lines=0.01 \
    --top_k_recall_by_pred_prob=0.2 \
    --reasoning_method=all \
    --train_data_file=../data/reposvul_dataset/train.csv \
    --eval_data_file=../data/reposvul_dataset/val.csv \
    --test_data_file=../data/reposvul_dataset/test.csv \
    --block_size 512 \
    --eval_batch_size 512 > "test_with_reposvul_rq3.log" 2>&1

for llm in "${llms[@]}"; do
    echo ">>> Testing mit $llm"
    python linevul_main.py \
        --model_name=model.bin \
        --output_dir=./saved_models_with_"$llm" \
        --model_type=roberta \
        --tokenizer_name=microsoft/codebert-base \
        --model_name_or_path=microsoft/codebert-base \
        --do_test \
        --do_sorting_by_line_scores \
        --effort_at_top_k=0.2 \
        --top_k_recall_by_lines=0.01 \
        --top_k_recall_by_pred_prob=0.2 \
        --reasoning_method=all \
        --train_data_file=../data/reposvul_with_"$llm"/train_aug.csv \
        --eval_data_file=../data/reposvul_dataset/val.csv \
        --test_data_file=../data/reposvul_dataset/test.csv \
        --block_size 512 \
        --eval_batch_size 512 > "test_with_${llm}_rq3.log" 2>&1
done


