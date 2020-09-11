for i in {1..15}; do
	sbatch 3_5_activity_matrix.sbatch $i
done
