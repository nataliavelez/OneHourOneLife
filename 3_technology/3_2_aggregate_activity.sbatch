#!/bin/bash
#
#SBATCH -p shared
#SBATCH --mem 64000
#SBATCH -t 01:00:00
#SBATCH -o reports/agg.%j.out
#SBATCH -e reports/agg.%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 3_2_aggregate_activity.py
