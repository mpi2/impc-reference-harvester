# IMPC Reference harvester
IMPC harvester for comsortium's resources citing papers

## Requirements
- [Python 3+](https://www.python.org/)
- [MongoDB] (https://www.mongodb.com/)
- [Solr](http://lucene.apache.org/solr/) with the [Allele2 core](https://goo.gl/H9Mqgy) loaded

## How to run

1. Clone this repo:
  ```
  git clone https://github.com/mpi2/impc-reference-harvester.git
  cd impc-reference-harvester
  ```
2. Edit the **config_example.ini** file.
3. Create a new pyvenv and activate it:
  ```
  python3 -m venv .venv
  source .venv/bin/activate
  ```
3. Install python dependecies:
  ```
  pip install -r requirements.txt
  ```
4. Run the script:
  ```
  python reference_harvester.py 
  ```
 
## Development environment setup
