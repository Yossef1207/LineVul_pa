#!/bin/bash -l
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 1
#SBATCH --mail-type=ALL
#SBATCH --mail-user=yossef.albuni@tuhh.de
#SBATCH --time 1:00:00

#SBATCH --gres gpu:1
#SBATCH --mem-per-gpu 75000
#SBATCH --output output/%x_%j.log

# Lokales Arbeits- und Eingabeverzeichnis definieren
WORKDIR=$SCRATCH/$SLURM_JOB_ID
INPUTDIR=$SLURM_SUBMIT_DIR

mkdir -p "$WORKDIR"

# Caches auf das lokale Verzeichnis legen (wichtig fuer HF, Pip, Triton)
export HF_HOME=$WORKDIR/hf_cache
export PIP_CACHE_DIR=$WORKDIR/pip_cache
export TRITON_HOME=$WORKDIR/triton

mkdir -p "$HF_HOME" "$PIP_CACHE_DIR" "$TRITON_HOME"

# Benoetigte Daten/Code auf die lokale Platte kopieren
cp -r "$INPUTDIR/linevul" "$WORKDIR/"
cp -r "$INPUTDIR/data" "$WORKDIR/"

# Load anaconda und aktiviere das linevul-Env korrekt im Batch-Skript
module load anaconda/2023.07-1
eval "$(conda shell.bash hook)"
conda activate linevul

nproc_per_node=1

########################   ReposVul Training   ########################

cd "$WORKDIR/linevul"

python linevul_main.py \
    --output_dir=./saved_models_with_reposvul \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --do_train \
    --do_test \
    --train_data_file=$WORKDIR/data/reposvul_dataset/train.csv \
    --eval_data_file=$WORKDIR/data/reposvul_dataset/val.csv \
    --test_data_file=$WORKDIR/data/reposvul_dataset/test.csv \
    --epochs 10 \
    --block_size 512 \
    --train_batch_size 16 \
    --eval_batch_size 16 \
    --learning_rate 2e-5 \
    --max_grad_norm 1.0 \
    --evaluate_during_training \
    --seed 123456  2>&1 | tee "train_with_reposvul_only.log"

llms=(codellama gpt-4o)

for llm in "${llms[@]}"; do
  echo ">>> Training with $llm"

  python linevul_main.py \
    --output_dir=./saved_models_with_reposvul_"$llm" \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --do_train \
    --do_test \
    --train_data_file=$WORKDIR/data/reposvul_with_"$llm"/train_aug.csv \
    --eval_data_file=$WORKDIR/data/reposvul_dataset/val.csv \
    --test_data_file=$WORKDIR/data/reposvul_dataset/test.csv \
    --epochs 10 \
    --block_size 512 \
    --train_batch_size 16 \
    --eval_batch_size 16 \
    --learning_rate 2e-5 \
    --max_grad_norm 1.0 \
    --evaluate_during_training \
    --seed 123456  2>&1 | tee "train_with_reposvul_${llm}.log"
done

# Ergebnisse und Logs zurueck ins Einabeverzeichnis kopieren
cp -r "$WORKDIR/linevul/saved_models_with_reposvul"* "$INPUTDIR/linevul/" 2>/dev/null || true
cp "$WORKDIR/linevul"/train_with_reposvul_*.log "$INPUTDIR/linevul/" 2>/dev/null || true

########################   PrimeVul Training   ########################

cd "$WORKDIR/linevul"

python linevul_main.py \
			--output_dir=./saved_models_with_primevul \
			--model_type=roberta \
			--tokenizer_name=microsoft/codebert-base \
			--model_name_or_path=microsoft/codebert-base \
			--do_train \
			--do_test \
			--train_data_file=$WORKDIR/data/primevul_dataset/train.csv \
			--eval_data_file=$WORKDIR/data/primevul_dataset/val.csv \
			--test_data_file=$WORKDIR/data/primevul_dataset/test.csv \
			--epochs 10 \
			--block_size 512 \
			--train_batch_size 16 \
			--eval_batch_size 16 \
			--learning_rate 2e-5 \
			--max_grad_norm 1.0 \
			--evaluate_during_training \
			--seed 123456  2>&1 | tee "train_with_primevul_only.log"

llms=(codellama gpt-4o)

for llm in "${llms[@]}"; do
	echo ">>> Training with $llm"

	python linevul_main.py \
		--output_dir=./saved_models_with_primevul_"$llm" \
		--model_type=roberta \
		--tokenizer_name=microsoft/codebert-base \
		--model_name_or_path=microsoft/codebert-base \
		--do_train \
		--do_test \
		--train_data_file=$WORKDIR/data/primevul_with_"$llm"/train_aug.csv \
		--eval_data_file=$WORKDIR/data/primevul_dataset/val.csv \
		--test_data_file=$WORKDIR/data/primevul_dataset/test.csv \
		--epochs 10 \
		--block_size 512 \
		--train_batch_size 16 \
		--eval_batch_size 16 \
		--learning_rate 2e-5 \
		--max_grad_norm 1.0 \
		--evaluate_during_training \
		--seed 123456  2>&1 | tee "train_with_primevul_${llm}.log"
done

# Ergebnisse und Logs zurueck ins Einabeverzeichnis kopieren
cp -r "$WORKDIR/linevul/saved_models_with_primevul"* "$INPUTDIR/linevul/" 2>/dev/null || true
cp "$WORKDIR/linevul"/train_with_primevul_*.log "$INPUTDIR/linevul/" 2>/dev/null || true

# Aufraeumen
rm -rf "$WORKDIR"

exit 0
