#!/bin/bash
#
#SBATCH -p shared
#SBATCH --mem 32000
#SBATCH -t 36:00:00
#SBATCH -o reports/distance_%j.out
#SBATCH -e reports/distance_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

module load Anaconda3/5.0.1-fasrc01
source activate ohol_py3
python spatial_proximity.py
