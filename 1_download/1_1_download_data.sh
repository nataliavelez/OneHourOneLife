#!/bin/bash
#
#SBATCH -p ncf
#SBATCH --mem 16000
#SBATCH -t 5
#SBATCH -o reports/download_%j.out
#SBATCH -e reports/download_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 1_1_download_data.py
