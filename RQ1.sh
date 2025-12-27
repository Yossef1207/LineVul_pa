#!/bin/bash -l
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 1
#SBATCH --mail-type=ALL
#SBATCH --mail-user=yossef.albuni@tuhh.de
#SBATCH --time 1-00:00:00

#SBATCH --gres gpu:1
#SBATCH --mem 48G
#SBATCH --output output/training_test.log

# Load anaconda und aktiviere das linevul-Env korrekt im Batch-Skript
module load anaconda/2023.07-1
eval "$(conda shell.bash hook)"
conda activate linevul

nproc_per_node=1

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
    --train_data_file=../data/reposvul_dataset/train.csv \
    --eval_data_file=../data/reposvul_dataset/val.csv \
    --test_data_file=../data/big-vul_dataset/test.csv \
    --block_size 512 \
    --eval_batch_size 512 > "test_with_reposvul_rq1.log" 2>&1


for llm in "${llms[@]}"; do
    echo ">>> Testing mit $llm"
    python linevul_main.py \
    --model_name=model.bin \
    --output_dir=./saved_models_with_"$llm" \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --do_test \
    --train_data_file=../data/reposvul_with_"$llm"/train_aug.csv \
    --eval_data_file=../data/reposvul_dataset/val.csv \
    --test_data_file=../data/big-vul_dataset/test.csv \
    --block_size 512 \
    --eval_batch_size 512 > "test_with_${llm}_rq1.log" 2>&1
done

