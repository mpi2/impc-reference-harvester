# IMPC Reference harvester
IMPC harvester for comsortium's resources citing papers

## Requirements
- [Python 3+](https://www.python.org/)
- [MongoDB] (https://www.mongodb.com/)
- [Solr](http://lucene.apache.org/solr/) with the [Allele2 core](https://goo.gl/H9Mqgy) loaded

## How to run

1. Clone this repo:
  ```console
  git clone https://github.com/mpi2/impc-reference-harvester.git
  cd impc-reference-harvester
  ```
2. Edit the **config_example.ini** file.
3. Create a new pyvenv and activate it:
  ```console
  python3 -m venv .venv
  source .venv/bin/activate
  ```
4. Install python dependecies:
  ```console
  pip install -r requirements.txt
  ```
5. Run the script:
  ```console
  python reference_harvester.py 
  ```
 
## Development environment setup


## Development environment setup
1. Install [Spark 2+](https://spark.apache.org/) and remember to set the ``SPARK_HOME`` environment variable.
2. Fork this repo and then clone your forked version:
    ```console
    git clone https://github.com/USERNAME/impc-reference-harvester.git
    cd impc-reference-harvester
    ```
3. Use your favorite IDE to make your awesome changes and make sure the project is pointing to the venv generated.
To do that using Pycharm fo to the instructions [here](https://www.jetbrains.com/help/pycharm/configuring-python-interpreter.html).

4. And finally commit and push your changes to your fork and the make a pull request to the original repo when you are ready to go.
Another member of the team will review your changes and after having two +1 you will be ready to merge them to the base repo.

    In order to sync your forked local version with the base repo you need to add an _upstream_ remote:

    ```console
    git remote add upstream https://github.com/mpi2/impc-reference-harvester.git
    ```
    
    Please procure to have your version in sync with the base repo to avoid merging hell.

    ```console
    git fetch upstream
    git checkout master
    git merge upstream/master
    git push origin master
    ```
