![logo](static/images/MASTER_logo_notext.jpg)
##this is a server for MASTER##
Method of Accelerated Search for Tertiary Ensemble Representatives

This has two components:

   - a Flask based web app that serves up an API for running
master on a server.
   - a PyMol Plugin that provides an interface for easily sending requests to the server search api.

###prerequisites:###
on osx install:

  - install [homebrew](http://brew.sh) if you don't have it
  - `brew install redis`
  - start redis:
  - `redis-server /usr/local/etc/redis.conf`
  - `pip install flask rq gunicorn`
  - `git clone git@github.com:timofei7/master_protein.git`
  - install master and msl in the `external` directory
  	- precompiled MSL for osx version available [here]( http://grigoryanlab.org/msl/msl-static-MacOSX_1.2.2.7.tar.gz)
  	- master available [here](http://grigoryanlab.org/master)
  - download the pdb library available here INSERT_LINK
  - edit the Settings.py file to match your paths
  - edit `pymol/Master/__init__.py` and make sure the URL points to either:
  	- `http://127.0.0.1:5000/api/search` for local development
  	- or `http://ararat.cs.dartmouth.edu:5000/api/search` for hitting the "production" server. 

###run it:###
to run a local server simply do:

  - `./run` 
  
This will launch a server at `http://127.0.0.1:5000` which will serve up a basic html page as well as the `http://127.0.0.1:5000/api/` endpoints which the PyMol module will hit. 

  - open PyMol and add the directory `/path/to/your/repo/pymol/` to *Plugin->Plugin Manager->Settings->Add New Directory*.  Then restart PyMol.   This will autoload the plugin and if you make any code changes all you need to do is restart PyMol. 

###contribute to it:###
  - `pymol/Master` contains the pymol plugin module
  - `testing/` contains some basic test scripts
  - `MasterApp.py` is the main flask app with various worker classes in the same directory.
  - use github issues and pull requests [github page](https://github.com/timofei7/master_protein)

###test scripts###

test files in: `testing`

  - `testing/test.py`

