#!/bin/bash
#
#SBATCH -p ncf_bigmem
#SBATCH --mem 128000
#SBATCH -t 5:00:00
#SBATCH -o reports/svd.%j.out
#SBATCH -e reports/svd.%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 3_6_svd.py
