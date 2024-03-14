#!/bin/bash

##Job Script for FYP

#SBATCH --partition=SCSEGPU_UG
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --qos=normal
#SBATCH --mem=32G
#SBATCH --job-name=TGSRec_Jupyter
#SBATCH --output=/home/FYP/siddhant005/fyp/train_sh_scripts/slurm_logs/output_%x_%j.out
#SBATCH --error=/home/FYP/siddhant005/fyp/train_sh_scripts/slurm_logs/error_%x_%j.err

module load anaconda
module load cuda/12.1
source activate retagnn_pyg
which python
jupyter-notebook --ip=$(hostname -i) --port=8885