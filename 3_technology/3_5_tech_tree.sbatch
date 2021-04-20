#!/bin/bash
#
#SBATCH -p shared
#SBATCH --mem 8000
#SBATCH -t 03:00:00
#SBATCH -o reports/tree.%j.out
#SBATCH -e reports/tree.%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 3_5_tech_tree.py
