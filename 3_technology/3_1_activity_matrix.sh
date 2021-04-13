for i in {0..16}; do
	sbatch 3_1_activity_matrix.sbatch $i
done
