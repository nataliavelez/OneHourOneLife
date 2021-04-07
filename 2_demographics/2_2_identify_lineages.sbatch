#!/bin/bash
#
#SBATCH -p shared
#SBATCH --mem 16000
#SBATCH -t 04:00:00
#SBATCH -o reports/lineages_%j.out
#SBATCH -e reports/lineages_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 2_2_identify_lineages.py
