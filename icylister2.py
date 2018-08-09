#!/usr/bin/env python3
import sys
import json

from urllib.request import Request, urlopen
from datetime import datetime


class IcyLister2:
    """
    Helper class to get and parse Icecast MP3 Stream Metadata.

    Documentation for parsing the metadata: http://www.smackfu.com/stuff/programming/shoutcast.html
    (Seems like Icecast and Shoutcast are compatible here...)
    """
    _stream = None
    _meta_interval = None

    def __init__(self, stream_url, user_agent="VLC/2.2.4 LibVLC/2.2.4"):
        """
        Open the stream by performing the HTTP request. Constructed object can be used to extract the streams metadata.
        :param stream_url: HTTP URL where the stream can be found.
        :param user_agent: Optional. User-Agent to supply to the server. Defaults to 'VLC/2.2.4 LibVLC/2.2.4'.
        """
        request = Request(stream_url, headers={"Icy-MetaData": "1",
                                               "User-Agent": user_agent})
        self._stream = urlopen(request)

        for header, value in self._stream.getheaders():
            if header.lower() == "icy-metaint":
                meta_interval = int(value)
        try:
            meta_interval
        except NameError:
            raise RuntimeError("Server did NOT respond with a \'Icy-Metaint\' header. "
                               "This makes it impossible to extract metadata "
                               "(we do not know which frames hold metadata). "
                               "Are you sure the server we're talking to is an Icecast (... compatible thingy)?")

        self._meta_interval = meta_interval

    def close(self):
        """
        Closes the stream and sets the stream and meta_interval instance vars to `None`.
        :return: Nothing.
        """
        self._stream.close()
        self._stream = None
        self._meta_interval = None

    @staticmethod
    def parse_icy_metadata(data_string):
        """
        Parses Icecast metadata from a data_string into a dict.
        :param data_string: The extracted metadata, as string.
        :return: dict mapping tag to value, `None` if data_string is empty.
        """
        metadata = {}

        current_tag = ""
        current_value = ""
        reading_tag = True

        for char in data_string:
            if reading_tag:  # Are we currently reading what should be part of a tag
                if char == '=':
                    reading_tag = False
                else:
                    current_tag += char
            else:  # Currently reading value field
                if char == ';':
                    if current_value[0] == "'" and current_value[-1] == "'":
                        # Cut away the "'" at the beginning and end if they exist.
                        current_value = current_value[1:-1]
                    metadata[current_tag] = current_value
                    current_tag = ""
                    current_value = ""
                    reading_tag = True
                else:
                    current_value += char
        return metadata

    def get_metadata_once(self):
        """
        Read `self.meta_internal` bytes from the stream, than read the metadata and parse it.
        If the metadata has length 0 (= the server did not include any metadata as it has not changed), return `None`.
        :return: the parsed metadata as a dict (achieved by calling `self.parse_icy_metadata` on the read metadata),
        or `None` if no metadata was set this time.
        """
        self._stream.read(self._meta_interval)  # Eat the useless mp3 data
        meta_len = int.from_bytes(self._stream.read(1), 'big') * 16
        if meta_len > 0:
            meta_data = self._stream.read(meta_len).replace(b"\x00", b"")
            meta_data = meta_data.decode("Windows-1252")  # Default western code page? Seems to work, so...
            return self.parse_icy_metadata(meta_data)

    def get_next_metadata(self):
        """
        Call `self.get_metadata_once` until we get actually get metadata (basically until the metadata changes and the
        server sends a new metadata block.
        :return: The next parsed metadata, as dict.
        """
        result = None
        while result is None:
            result = self.get_metadata_once()
        return result


###
# CLI INTERFACE
###


def _pretty_print(icylister, printer_func, with_timestamp=True, filter_fields=None):
    """
    Reads the stream until the next metadata block appears and optionally enriches it with the current timestamp.
    Than calls the printer function to print the metadata. Does this until KeyboardInterrupt is received.
    You must close the icylister object yourself afterwards, this function does not open / close the object.
    :param icylister: Icylister instance with open stream.
    :param printer_func: Function to call to print the metadata,gets a dict with the parsed data as first and only
        argument.
    :param with_timestamp: if `True` a field `_timestamp` in `datetime.now()` format is included in the result.
    :param filter_fields: Array of fields you want to filter for, if empty all fields are given to the printer.
    :return: None
    """

    try:
        while True:
            # Get the metadata once
            metadata = icylister.get_next_metadata()
            if filter_fields is None or len(filter_fields) == 0:
                result = metadata
            else:
                result = {}
                for key, value in metadata:
                    if key in filter_fields:
                        result[key] = value

            if with_timestamp:
                result["_timestamp"] = str(datetime.now())

            # Hand the data to the printer for printing
            printer_func(result)
    except KeyboardInterrupt:
        pass


def _pretty_printer_yaml(metadata):
    for field in metadata:
        print(field + ": " + metadata[field])
    print("---")


def _pretty_printer_json(metadata):
    json.dump(metadata, sys.stdout)
    print()


_printer_map = {
    'yaml': _pretty_printer_yaml,
    'json': _pretty_printer_json
}


# actual main()
def main():
    # TODO: Fix this arg parsing
    url = sys.argv[1]
    printer = _printer_map[sys.argv[2]]

    instance = IcyLister2(url)
    # TODO: Cmd-line args for with_timestamp and filter_fields
    _pretty_print(instance, printer, with_timestamp=True, filter_fields=None)
    instance.close()


# if __name__ == "__main__" handler for running the script via python SCRIPT_NAME or ./SCRIPT_NAME
if __name__ == "__main__":
    main()


# __main__ for running the script via python -m MODULE_NAME
def __main__():
    main()
