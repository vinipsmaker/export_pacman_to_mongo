# import_pacman_to_mongo.py

`import_pacman_to_mongo` is a Python 3 script that will gather information about
your local pacman database (using the pacman executable), convert the
information to a nice and queryable format and upload it to MongoDB
(`{"db": "pacman", "collection": "packages"}`).

# Dependencies

The script dependencies:

* Python 3.
* [python-dateutil](http://labix.org/python-dateutil).
* [python-pymongo](https://pypi.python.org/pypi/pymongo/).
* `en_US.UTF-8` must be installed, but it doesn't need to be the default locale.
* The locale you use to run the script within must be any `UTF-8`-based locale.

# ROADMAP

* Parse command-line arguments.
  * Support to different MongoDB database IDs.
  * Support to different MongoDB collection IDs.
  * Output data to JSON. Dates must be handled correctly.
* Define a JSON schema to help dude to understand what fields dude should expect
  in the documents.
* Rename `name` to `_id` (?).
* Gather package's origin (repo).

# LICENSE

The script is lincensed under the MIT license. I don't care about its use.
