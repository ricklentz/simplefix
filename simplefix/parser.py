#! /usr/bin/env python
########################################################################
# SimpleFIX
# Copyright (C) 2016-2017, David Arnold.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

from .message import FixMessage, SOH


class FixParser(object):
    """FIX protocol message parser.

    This class translates FIX application messages in raw (wire)
    format into instance of the FixMessage class.

    It does not perform any validation of the fields, their presence
    or absence in a particular message, the data types of fields, or
    the values of enumerations.

    It is suitable for streaming processing, accumulating byte data
    from a network connection, and returning complete messages as they
    are delivered, potentially in multiple fragments."""

    def __init__(self):
        """Constructor."""
        self.reset()
        return

    def reset(self):
        """Reset the internal parser state.

        This will discard any appended buffer content, and any fields
        parsed so far."""

        # Internal buffer used to accumulate message data.
        self.buf = ''

        # Parsed "tag=value" pairs, removed from the buffer, but not
        # yet returned as a message.
        self.pairs = []
        return

    def append_buffer(self, buf):
        """Append a character string to the parser buffer.

        :param buf: byte string to append.

        The parser maintains an internal buffer of bytes to be parsed.
        As raw data is read, it can be appended to this buffer.  Each
        call to get_message() will try to remove the bytes of a
        complete messages from the head of the buffer."""
        self.buf += buf
        return

    def get_buffer(self):
        """Return a copy of the internal buffer."""
        return self.buf

    def get_message(self):
        """Process the accumulated buffer and return the first message.

        If the buffer starts with FIX fields other than BeginString
        (8), these are discarded until the start of a message is
        found.

        If no BeginString (8) field is found, this function returns
        None.  Similarly, if (after a BeginString) no Checksum (10)
        field is found, the function returns None.

        Otherwise, it returns a simplefix.FixMessage instance
        initialised with the fields from the first complete message
        found in the buffer."""

        # Break buffer into tag=value pairs.
        pairs = self.buf.split(SOH)
        if len(pairs) > 0:
            self.pairs.extend(pairs[:-1])
            if pairs[-1] == '':
                self.buf = ''
            else:
                self.buf = pairs[-1]

        if len(self.pairs) == 0:
            return None

        # Check first pair is FIX BeginString.
        while self.pairs and self.pairs[0][:6] != "8=FIX.":
            # Discard pairs until we find the beginning of a message.
            self.pairs.pop(0)

        if len(self.pairs) == 0:
            return None

        # Look for checksum.
        index = 0
        while index < len(self.pairs) and self.pairs[index][:3] != "10=":
            index += 1

        if index == len(self.pairs):
            return None

        # Found checksum, so we have a complete message.
        m = FixMessage()
        m.append_strings(self.pairs[:index + 1])
        self.pairs = self.pairs[index + 1:]

        return m


########################################################################
