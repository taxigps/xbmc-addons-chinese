#
#  Util/PEM.py : Privacy Enhanced Mail utilities
#
# ===================================================================
#
# Copyright (c) 2014, Legrandin <helderijs@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ===================================================================

"""Set of functions for encapsulating data according to the PEM format.

PEM (Privacy Enhanced Mail) was an IETF standard for securing emails via a
Public Key Infrastructure. It is specified in RFC 1421-1424.

Even though it has been abandoned, the simple message encapsulation it defined
is still widely used today for encoding *binary* cryptographic objects like
keys and certificates into text.
"""

__all__ = ['encode', 'decode']

from Crypto.Util.py3compat import b, hexlify, unhexlify, tobytes, tostr

import re
from binascii import a2b_base64, b2a_base64


def decode(pem_data, passphrase=None):
    """Decode a PEM block into binary.

    :Parameters:
      pem_data : string
        The PEM block.
      passphrase : byte string
        If given and the PEM block is encrypted,
        the key will be derived from the passphrase.
    :Returns:
      A tuple with the binary data, the marker string, and a boolean to
      indicate if decryption was performed.
    :Raises ValueError:
      If decoding fails, if the PEM file is encrypted and no passphrase has
      been provided or if the passphrase is incorrect.
    """

    # Verify Pre-Encapsulation Boundary
    r = re.compile("\s*-----BEGIN (.*)-----\s+")
    m = r.match(pem_data)
    if not m:
        raise ValueError("Not a valid PEM pre boundary")
    marker = m.group(1)

    # Verify Post-Encapsulation Boundary
    r = re.compile("-----END (.*)-----\s*$")
    m = r.search(pem_data)
    if not m or m.group(1) != marker:
        raise ValueError("Not a valid PEM post boundary")

    # Removes spaces and slit on lines
    lines = pem_data.replace(" ", '').split()

    # Decode body
    data = a2b_base64(b(''.join(lines[1:-1])))
    enc_flag = False

    return (data, marker, enc_flag)
