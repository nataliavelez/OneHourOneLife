#!/bin/bash
#
#SBATCH -p shared
#SBATCH --mem 16000
#SBATCH -t 5
#SBATCH -o reports/wrangling_%j.out
#SBATCH -e reports/wrangling_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 2_0_wrangling.py
