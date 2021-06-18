#!/bin/bash
#SBATCH --job-name NMF-cleaned
#SBATCH --time 48:0:0
#SBATCH --partition long
#SBATCH --cpus-per-task 1
#SBATCH --mem 60g
#SBATCH -o /home/mpib/cwu/OneHourOneLife/logs/nmf-cleaned.out
#SBATCH --workdir .

python -u jobspace/validate_nmf.py -m cleaned > logs/cleaned.out
