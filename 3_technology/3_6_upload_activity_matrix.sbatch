#!/bin/bash
#
#SBATCH -p shared
#SBATCH --mem 128000
#SBATCH -t 48:00:00
#SBATCH -o reports/upload.%j.out
#SBATCH -e reports/upload.%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate py3
python 3_6_upload_activity_matrix.py
