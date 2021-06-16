#!/bin/bash
#SBATCH --job-name NMF
#SBATCH --time 36:0:0
#SBATCH --cpus-per-task 1
#SBATCH --mem 60g
#SBATCH -o /home/mpib/cwu/OneHourOneLife/logs/nmf.out
#SBATCH --workdir .

python -u jobspace/validate_nmf.py > logs/validate.out
