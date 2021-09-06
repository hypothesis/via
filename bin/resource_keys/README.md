How to use this
===============

* Add your lists of urls to `data/*.csv`
* Add a `data/credentials.json` file
* This should be a `list` of credentials (the more you add from different
  accounts the faster it goes)
* `../../.tox/dev/bin/pip install -r bin/resource_keys/requirements.txt`
* Run the scripts in order:
    * `../../.tox/dev/bin/python 01_extract_urls.py`
    * etc.

Getting data
------------

For `h`:

```sql
select distinct(target_uri) from annotation where target_uri like '%://drive.google.com/uc?id=%&export=download%'
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
