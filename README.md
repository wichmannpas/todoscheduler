TodoScheduler [![Build Status](https://travis-ci.org/wichmannpas/todoscheduler.svg?branch=master)](https://travis-ci.org/wichmannpas/todoscheduler) [![codecov](https://codecov.io/gh/wichmannpas/todoscheduler/branch/master/graph/badge.svg)](https://codecov.io/gh/wichmannpas/todoscheduler)
================================================================================================================================================================================================================================================================================================

TodoScheduler helps you managing and scheduling your tasks. You can split your tasks into chunks and schedule them for specific days.
Scheduling all of your tasks means less postponed tasks and a higher productivity. That means more free time!

This repository contains the backend of TodoScheduler (i.e., an API endpoint).
There is a JavaScript [web client](https://github.com/wichmannpas/todoscheduler-webclient) that can be used as a frontend for TodoScheduler.

Installation
------------

The installation is that of a common Django app. Basically, the following steps are required (for advanced configuration as well as a production-suitable database, see the official [Django documentation](https://docs.djangoproject.com/)):

Create a virtual environment and activate it:

```
python3 -m venv .pyenv
. .pyenv/bin/activate
```

Install the dependencies:

```
pip install -r requirements.txt
```

Copy the example settings:

```
cp todoscheduler/settings.py{.example.sqlite,}
```

Migrate the database:

```
./manage.py migrate
```

Run the development server (again, see the official documentation for production-suitable deployments):

```
./manage.py runserver
```

Cron
----

For the scheduling of task chunk series, you need to run the following regularly (e.g., once daily):

```
./manage.py scheduletaskchunkseries
```

Demo
----

A hosted instance of TodoScheduler is available [here](https://todoscheduler.org).

License
-------

Copyright 2017 Pascal Wichmann

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
