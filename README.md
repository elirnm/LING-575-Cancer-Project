Histologic Grade Classification
-----

### Eli Miller, Will Kearns, Krista Watkins
#### LING 575C: Natural Language Processing in Cancer Informatics, Winter 2017, University of Washington

Usage
-----

Update config.py to contain the location of your MetaMap Lite directory, then run:

Windows (assumes the default Python is Python 3):
```
run.cmd data_dir print-errors no-metamap full-results
```
Unix:
```bash
run.sh data_dir print-errors no-metamap full-results
```
Manually:
```bash
python(3) main.py data_dir print-errors no-metamap full-results
```

data_dir is the directory containing the data files.

print-errors is an optional string. If it is present, error data will be printed to an "error_analysis.txt" file.

no-metamap is an optional string. If it is present, MetaMap Lite will not be used.

full-results is an optional string. If it is present, the program will print results for each module as well as combined results.

Dependencies
-----

* Python 3
* scikit-learn
* MetaMap Lite (optional)
