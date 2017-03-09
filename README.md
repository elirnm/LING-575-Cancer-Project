Histologic Grade Classification
-----

### Eli Miller, Will Kearns, Krista Watkins
#### LING 575C: Natural Language Processing in Cancer Informatics, Winter 2017, University of Washington

This program classifies patient clinical records for histologic grade.

Usage
-----

Update config.py to contain the location of your MetaMap Lite directory (if you want to use it), then run:

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

data_dir is the directory containing the data files (the clinical records, not the annotations).

print-errors is an optional string. If it is present, error data will be printed to an "error_analysis.txt" file.

no-metamap is an optional string. If it is present, MetaMap Lite will not be used.

full-results is an optional string. If it is present, the program will print results for each module as well as combined results. This produces 188 lines of output, so it's recomended to send output to a file if you use it.

Results are sent to standard out.

Dependencies
-----

* Python 3
* [scikit-learn](http://scikit-learn.org/stable/index.html)
* [MetaMap Lite (optional)](https://metamap.nlm.nih.gov/MetaMapLite.shtml)
