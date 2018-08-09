# IcyLister 2
A small utility script that is able to fetch an Icecast MP3 stream and
extract its metadata, printing it ```stdout``` with the help of various
(OK, two at the moment) pretty printers.

```
usage: icylister2.py [-h] [-t] [-s FIELD] url {yaml,json}

positional arguments:
  url                   The URL of the Icecast (compatible) MP3 stream.
  {yaml,json}           Name of the pretty printer to use.

optional arguments:
  -h, --help            show this help message and exit
  -t, --with-timestamp  Include a '_timestamp' field with the current
                        datetime.now() in the output.
  -s FIELD, --select-fields FIELD
                        When given at least once, filter the output to only
                        include the selected fields. If used in combination
                        with -t / --with-timestamp, the timestamp is always
                        included.

```
