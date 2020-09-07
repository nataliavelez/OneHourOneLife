#!/bin/bash
#
#SBATCH -p ncf
#SBATCH --mem 16000
#SBATCH -t 30
#SBATCH -o reports/wrangling_%j.out
#SBATCH -e reports/wrangling_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 3_1_wrangling.py
