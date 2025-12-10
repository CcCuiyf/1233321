# README

## What is this repository for?
This repository contains source code for heirarichal classifer using methylation data. Code is being migrated from a general classifiers

## Set up

### Instruction
The whole project was combined by 4 parts, which are Training, DifferentialMethylationClassifer, Grid Search and Parallel Training.

#### Working branch
on databricks, the working branch was like Workspace/{username}/{branchname}/src/mch

#### Training
using Random Forest as base model, relavent functions/file as below:

#### Training entrance
/mch/model/training.py

class BatchModelTrainer: the entrance of model training, using

trainer = BatchModelTrainer() stats = trainer.train_all_models(raise_on_error=raise_on_error)

to train the model.

#### Data load
/mch/config/setting.py

in function load_data, by change content of mvalue_df = pl.read_csv() to select different dataset

/mch/config/base_config.yaml

please modify the directory defined inside if want run the project on another branch

#### DifferentialMethylationClassifer
was defined in /model/DifferentialMethylation.R using limma and implement by /model/DifferentialMethylationClassifer.py

only thing to notice is check the cells above to confirm the R enviroment and package used was successfully installed

Changing the parameter disable_dm = True will disable DifferentialMethylationClassifer.

##### in case DifferentialMethylationClassifer was disable:
Will use top-k to filter feature, the algorithm was defined in /model/training.py, fuction train_all_model have a branch if disable_dm

in this case, if need to change the parameter of top-k, please go the parameter setting cell and change prefilter_* staff.

#### Grid Search
using GridSearchCV defined by sklearn, at /model/training.py

##### parameter grid
parameter grid was at /mch/config/model_training_config.yaml. And read by /mch/config/modelTrainingParameters.py

#### Parallel training

##### auto assign job
auto assign job/run using warking_branch/Assign_job, need parameters:

job_id: id of your job_cluster

if want train specific node, change cell 4/5, cell 4 is for train nodes that have more than 50 sample, cell 5 is for train node have specific name

if policy allow to assign more than 3 runs per time, change the cell 8 where len()==3

##### train note book
each job cluster using for parallel training need to use working_branch/Training_model_child

it will call BatchmodelTrainer in src/mch/model/traininig.py

### config files

if the structure of parameter in model_training_config.yaml was changed, need to change the last few lines in modelTrainingParameters.py to fit the new structure.
There should be set up instructions, yes.

scripts to find and generate data are in /data_processing. 
sample_file_generation.py generates files for new samples, it is currently run as a cron job nightly. Generated files will contain all probes for each sample, and are the base data file that is used as inputs to the filtering steps prior to model generation. sample_feature_collection selects the features that were identified as part of model training and adds them to a dataframe that is used to serve results.

- Summary of set up
- Configuration

Paths to credential files the config directory will need to be altered.
Paths for the base file locations will need to be updated in base_config.yaml

Dependencies Built and run using python 3.11 packages required are to be found in requirements.txt - this probably has packages over and above what is required. i.e. it could do with being cleaned.

Configuration. Currently, there are 3 places that one has to define which dataset to work on. I am currently using a variable called freeze, to define location. i.e. : /\<base data direcotry>/freeze\<monthyear>/ This needs to configured in the files

- mch.config.settings
- mch.core.create_disease_tree
- mch.data_processing.dataset_filtering I need to change this. At the moment, most other parts of this will pull from the settings. create_disease_tree and dataset_filtering have to be run prior to settings being able to work though

In later iterations, there should also probably be the ability to pass config files as part of the command line. Or at least a base directory. That's for when code is to be released/someone else needs to run it on a different system.

Database configuration In /db there are connectors to the sql database and to type db. These will need credentials. If we move this to databricks then I am assuming there will need to be additional code to mange access to the data.

How to run tests I do actually have some pytest tests. Not all of them run sucessfully as of yet.

Deployment instructions

## Contribution guidelines
- Writing tests
- Code review
- Other guidelines

##Who do I talk to?
Ben

