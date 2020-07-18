for i in {1..13}; do
	sbatch 3_5_activity_matrix.sbatch $i
done
