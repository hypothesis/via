How to use this
===============

* Add your lists of urls to `data/*.csv`
* Add a `data/credentials.json` file
* This should be a `list` of credentials (the more you add from different
  accounts the faster it goes)
* From the `bin/resource_keys` directory:
* `../../.tox/dev/bin/pip install -r requirements.txt`
* Run the scripts in order:
    * `../../.tox/dev/bin/python 01_extract_urls.py`
    * etc.

Getting data
------------

For `h` you can get updates using Metabase with:

```sql
select distinct(target_uri) from annotation where updated > '2021-08-16' and target_uri like '%://drive.google.com/uc?id=%&export=download%' and target_uri not like '%resource%'
```

For `LMS`:
```sql
select distinct document_url from module_item_configurations where document_url like '%drive.google.com%';
```

Doing updates
-------------

In `02_lookup.py` you can change the `should_refresh` condition:

```python
updater.get_worklist(should_refresh=RefreshReasons.file_id_is_new)
updater.get_worklist(should_refresh=RefreshReasons.quick_check)
updater.get_worklist(should_refresh=RefreshReasons.recheck)
```
