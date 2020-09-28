#!/bin/bash
#
#SBATCH -p ncf_bigmem
#SBATCH --mem 64000
#SBATCH -t 5:00:00
#SBATCH -o reports/svd_%j.out
#SBATCH -e reports/svd_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 3_6_svd.py
