#!/bin/bash
#
#SBATCH -p shared
#SBATCH --mem 16000
#SBATCH -t 01:30:00
#SBATCH -o reports/gen_%j.out
#SBATCH -e reports/gen_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate ohol_py3
python 2_3_detect_generations.py
