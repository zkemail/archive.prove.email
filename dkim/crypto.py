# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#
# Copyright (c) 2008 Greg Hewgill http://hewgill.com
#
# This has been modified from the original software.
# Copyright (c) 2011 William Grant <me@williamgrant.id.au>
# Copyright (c) 2018 Scott Kitterman <scott@kitterman.com>

__all__ = [
    'HASH_ALGORITHMS',
    'ARC_HASH_ALGORITHMS',
    ]

import hashlib


HASH_ALGORITHMS = {
    b'rsa-sha1': hashlib.sha1,
    b'rsa-sha256': hashlib.sha256,
    b'ed25519-sha256': hashlib.sha256
    }

ARC_HASH_ALGORITHMS = {
    b'rsa-sha256': hashlib.sha256,
    }

