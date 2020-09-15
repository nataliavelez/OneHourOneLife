#!/bin/bash
#
#SBATCH -p ncf
#SBATCH --mem 32000
#SBATCH -t 01:30:00
#SBATCH -o reports/discoveries_%j.out
#SBATCH -e reports/discoveries_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 3_4_discoveries.py
