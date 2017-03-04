Histologic Grade Classification
-----

### Eli Miller, Will Kearns, Krista Watkins
#### LING 575C: Natural Language Processing in Cancer Informatics, Winter 2017, University of Washington

Usage
-----

Update config.py to contain the location of your MetaMap Lite directory, then run:

Windows (assumes the default Python is Python 3):
```
run.cmd main.py data_dir error_file
```
Unix:
```bash
run.sh data_dir error_file
```
Manually:
```bash
python(3) main.py data_dir error_file
```

data_dir is the directory containing the data files.

error_file is optional. If it is present, error data will be printed to a file with that name.

Dependencies
-----

* Python 3
* MetaMap Lite
* scikit-learn
