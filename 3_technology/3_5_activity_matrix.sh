for i in {0..13}; do
	sbatch 3_5_activity_matrix.sbatch $i
done
