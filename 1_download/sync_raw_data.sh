SCRIPT_DIR=$PWD
DATA_DIR=../../data
cd $DATA_DIR

TO_DIR=/users/nvelezalicea/OneHourOneLife/data
find . -type f -path '*bigserver2*'  > sync_file_paths.txt
rsync -av --files-from=sync_file_paths.txt . nvelezalicea@ncflogin.rc.fas.harvard.edu:$TO_DIR
cd $SCRIPT_DIR
