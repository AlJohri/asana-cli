asana-cli
==========================

|PyPi Version| |License Status|

Python wrapper for asana. Requires Python 3.6+.

Install
-------

::

    pip3 install --upgrade asana-cli

CLI
---

::

    $ asana
    Usage: asana [OPTIONS] COMMAND [ARGS]...

      Examples:

      asana list workspaces
      asana list projects --workspace="Personal Projects"
      asana list tasks --workspace="Personal Projects" --project="Test"
      asana list sections --workspace="Personal Projects" --project="Test"
      asana list tasks --workspace="Personal Projects" --project="Test" --section="Column 1"

      asana delete tasks --workspace="Personal Projects" --project="Test" --section="Column 1"

      asana mark tasks --workspace="Personal Projects" --project="Test" --section="Column 1" --completed
      asana mark tasks --workspace="Personal Projects" --project="Test" --section="Column 1" --not-completed

      asana move tasks --workspace="Personal Projects" --from-project="Test" --from-section="Column 1" --to-section="Column 2"

    Options:
      --help  Show this message and exit.

    Commands:
      delete
      list
      mark
      move

Usage
-------

Most command outputs `line json <http://jsonlines.org/>`_ and works well with the `jq <https://stedolan.github.io/jq/>`_ command line tool. 

Examples:

Create csv of tasks within a project where the columns are `id, name, section`.

::

  $ asana list tasks --workspace="Personal Projects" --project="Test" | jq -r '[.id,.name,.memberships[].section.name] | @csv' > tasks.csv


Development
-----------

Setup
~~~~~

::

    make install

Test
~~~~

::

    make test

.. |PyPI Version| image:: https://img.shields.io/pypi/v/asana-cli.svg
   :target: https://pypi.python.org/pypi/asana-cli
.. |License Status| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://raw.githubusercontent.com/AlJohri/asana-cli/master/LICENSE
