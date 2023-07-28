#### submit_job.sh START ####
#!/bin/bash
#$ -cwd
# error = Merged with joblog
#$ -o joblog.$JOB_ID
#$ -j y

# request resources:
#$ -l highp,h_rt=3:00:00,h_data=8G
#$ -pe shared 1

# email address to notify
#$ -M $caderanek@ucla.edu
#$ -m bea

# load the job environment:
. /u/local/Modules/default/init/modules.sh


module load anaconda3
conda create -n $1
conda activate $1
conda install -c conda-forge plotnine -y
conda install -c conda-forge rioxarray -y
conda install ipykernel -y 
conda install hvplot.xarray -y 
conda install glob -y
conda install holoviews -y
python -m ipykernel install --user --name=$1 --display-name “$1”
