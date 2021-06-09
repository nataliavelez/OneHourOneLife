#!/bin/bash

for inputMatrix in cleaned tfidf ; do
	for numDims in $(seq -w 5 30) ; do
	    echo '#!/bin/bash'                    > job.slurm
	    echo "#SBATCH --job-name nmf_$inputMatrix_$numDims"  >> job.slurm
	    echo "#SBATCH --time 6:0:0"              >> job.slurm
	    echo "#SBATCH --mem 42g"              >> job.slurm
	    echo "#SBATCH --cpus-per-task 1"              >> job.slurm
	    echo "#SBATCH --workdir ."              >> job.slurm
	    echo "#SBATCH -o /home/mpib/cwu/OneHourOneLife/logs/nmf_$inputMatrix_$numDims.out"              >> job.slurm
	    echo "source /etc/bash_completion.d/virtualenvwrapper"              >> job.slurm
	    echo "workon ohol"              >> job.slurm
	    echo "python jobspace/validate_nmf.py -d $numDims -m $inputMatrix"           >> job.slurm
	    sbatch job.slurm
	    rm -f job.slurm
	done
done
