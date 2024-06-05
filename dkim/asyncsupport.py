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
#
# This has been modified from the original software.
# Copyright (c) 2016 Google, Inc.
# Contact: Brandon Long <blong@google.com>
#
# This has been modified from the original software.
# Copyright (c) 2016, 2017, 2018, 2019 Scott Kitterman <scott@kitterman.com>
#
# This has been modified from the original software.
# Copyright (c) 2017 Valimail Inc
# Contact: Gene Shuman <gene@valimail.com>

import asyncio
import aiodns
import base64
import dkim
import re

__all__ = [
    'get_txt_async',
    'load_pk_from_dns_async',
    'verify_async'
    ]


async def get_txt_async(name, timeout=5):
    """Return a TXT record associated with a DNS name in an asnyc loop. For
    DKIM we can assume there is only one."""

    # Note: This will use the existing loop or create one if needed
    loop = asyncio.get_event_loop()
    resolver = aiodns.DNSResolver(loop=loop, timeout=timeout)

    async def query(name, qtype):
        return await resolver.query(name, qtype)

    #q = query(name, 'TXT')
    try:
        result = await query(name, 'TXT')
    except aiodns.error.DNSError:
        result = None

    if result:
        return result[0].text
    else:
        return None


async def load_pk_from_dns_async(name, dnsfunc, timeout=5):
  s = await dnsfunc(name, timeout=timeout)
  pk, keysize, ktag, seqtlsrpt = dkim.evaluate_pk(name, s)
  return pk, keysize, ktag, seqtlsrpt

class DKIM(dkim.DKIM):
  #: Sign an RFC822 message and return the DKIM-Signature header line.
  #:
  #: Identical to dkim.DKIM, except uses aiodns and can be awaited in an
  #: ascyncio context.  See dkim.DKIM for details.

  # Abstract helper method to verify a signed header
  #: @param sig: List of (key, value) tuples containing tag=values of the header
  #: @param include_headers: headers to validate b= signature against
  #: @param sig_header: (header_name, header_value)
  #: @param dnsfunc: interface to dns
  async def verify_sig(self, sig, include_headers, sig_header, dnsfunc):
    name = sig[b's'] + b"._domainkey." + sig[b'd'] + b"."
    try:
      self.pk, self.keysize, self.ktag, self.seqtlsrpt = await load_pk_from_dns_async(name,
              dnsfunc, timeout=self.timeout)
    except dkim.KeyFormatError as e:
      self.logger.error("%s" % e)
      return False
    return self.verify_sig_process(sig, include_headers, sig_header, dnsfunc)


  async def verify(self,idx=0,dnsfunc=get_txt_async):
    prep = self.verify_headerprep(idx)
    if prep:
        sig, include_headers, sigheaders = prep
        return await self.verify_sig(sig, include_headers, sigheaders[idx], dnsfunc)
    return False # No signature


async def verify_async(message, logger=None, dnsfunc=None, minkey=1024,
        timeout=5, tlsrpt=False):
    """Verify the first (topmost) DKIM signature on an RFC822 formatted message in an asyncio contxt.
    @param message: an RFC822 formatted message (with either \\n or \\r\\n line endings)
    @param logger: a logger to which debug info will be written (default None)
    @param timeout: number of seconds for DNS lookup timeout (default = 5)
    @param tlsrpt: message is an RFC 8460 TLS report (default False)
    False: Not a tlsrpt, True: Is a tlsrpt, 'strict': tlsrpt, invalid if
    service type is missing. For signing, if True, length is never used.
    @return: True if signature verifies or False otherwise
    """
    # type: (bytes, any, function, int) -> bool
    # Note: This will use the existing loop or create one if needed
    loop = asyncio.get_event_loop()
    if not dnsfunc:
        dnsfunc=get_txt_async
    d = DKIM(message,logger=logger,minkey=minkey,timeout=timeout,tlsrpt=tlsrpt)
    try:
        return await d.verify(dnsfunc=dnsfunc)
    except dkim.DKIMException as x:
        if logger is not None:
            logger.error("%s" % x)
        return False
