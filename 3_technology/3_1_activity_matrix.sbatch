#!/bin/bash
#
#SBATCH -p shared
#SBATCH --mem 32000
#SBATCH -t 04:00:00
#SBATCH -o reports/mtx.%j.out
#SBATCH -e reports/mtx.%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=nvelez@fas.harvard.edu

# Build call to script
IDX=$1

# Call modeling script
module load Anaconda3
source activate py3
python 3_1_activity_matrix.py $IDX
