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
#


import base64
import logging
import re

# Set to False to not use async functions even though aiodns is installed.
USE_ASYNC = True

from dkim.canonicalization import (
    CanonicalizationPolicy,
    InvalidCanonicalizationPolicyError,
    )

from dkim.crypto import (
    HASH_ALGORITHMS,
    ARC_HASH_ALGORITHMS,
    )

from dkim.util import (
    get_default_logger,
    InvalidTagValueList,
    parse_tag_value,
    )

__all__ = [
    "DKIMException",
    "InternalError",
    "KeyFormatError",
    "MessageFormatError",
    "ParameterError",
    "ValidationError",
    "AuthresNotFoundError",
    "NaClNotFoundError",
    "DnsTimeoutError",
    "USE_ASYNC",
    "CV_Pass",
    "CV_Fail",
    "CV_None",
    "Relaxed",
    "Simple",
    "DKIM",
    "ARC",
    "sign",
    "verify",
    "dkim_sign",
    "dkim_verify",
    "arc_sign",
    "arc_verify",
]

Relaxed = b'relaxed'    # for clients passing dkim.Relaxed
Simple = b'simple'      # for clients passing dkim.Simple

# for ARC
CV_Pass = b'pass'
CV_Fail = b'fail'
CV_None = b'none'


class HashThrough(object):
  def __init__(self, hasher, debug=False):
    self.data = []
    self.hasher = hasher
    self.name = hasher.name
    self.debug = debug

  def update(self, data):
    if self.debug:
        self.data.append(data)
    return self.hasher.update(data)

  def digest(self):
    return self.hasher.digest()

  def hexdigest(self):
    return self.hasher.hexdigest()

  def hashed(self):
    return b''.join(self.data)


def bitsize(x):
    """Return size of long in bits."""
    return len(bin(x)) - 2


class DKIMException(Exception):
    """Base class for DKIM errors."""
    pass


class InternalError(DKIMException):
    """Internal error in dkim module. Should never happen."""
    pass


class KeyFormatError(DKIMException):
    """Key format error while parsing an RSA public or private key."""
    pass


class MessageFormatError(DKIMException):
    """RFC822 message format error."""
    pass


class ParameterError(DKIMException):
    """Input parameter error."""
    pass


class ValidationError(DKIMException):
    """Validation error."""
    pass


class AuthresNotFoundError(DKIMException):
    """ Authres Package not installed, needed for ARC """
    pass


class NaClNotFoundError(DKIMException):
    """ Nacl package not installed, needed for ed25119 signatures """
    pass

class UnknownKeyTypeError(DKIMException):
    """ Key type (k tag) is not known (rsa/ed25519) """

class DnsTimeoutError(DKIMException):
    """ DNS query for public key timed out """


def select_headers(headers, include_headers):
    """Select message header fields to be signed/verified.

    >>> h = [('from','biz'),('foo','bar'),('from','baz'),('subject','boring')]
    >>> i = ['from','subject','to','from']
    >>> select_headers(h,i)
    [('from', 'baz'), ('subject', 'boring'), ('from', 'biz')]
    >>> h = [('From','biz'),('Foo','bar'),('Subject','Boring')]
    >>> i = ['from','subject','to','from']
    >>> select_headers(h,i)
    [('From', 'biz'), ('Subject', 'Boring')]
    """
    sign_headers = []
    lastindex = {}
    for h in include_headers:
        assert h == h.lower()
        i = lastindex.get(h, len(headers))
        while i > 0:
            i -= 1
            if h == headers[i][0].lower():
                sign_headers.append(headers[i])
                break
        lastindex[h] = i
    return sign_headers


# FWS  =  ([*WSP CRLF] 1*WSP) /  obs-FWS ; Folding white space  [RFC5322]
FWS = br'(?:(?:\s*\r?\n)?\s+)?'
RE_BTAG = re.compile(br'([;\s]b'+FWS+br'=)(?:'+FWS+br'[a-zA-Z0-9+/=])*(?:\r?\n\Z)?')


def hash_headers(hasher, canonicalize_headers, headers, include_headers,
                 sigheader, sig):
    """Update hash for signed message header fields."""
    sign_headers = select_headers(headers,include_headers)
    # The call to _remove() assumes that the signature b= only appears
    # once in the signature header
    cheaders = canonicalize_headers.canonicalize_headers(
        [(sigheader[0], RE_BTAG.sub(b'\\1',sigheader[1]))])
    # the dkim sig is hashed with no trailing crlf, even if the
    # canonicalization algorithm would add one.
    for x,y in sign_headers + [(x, y.rstrip()) for x,y in cheaders]:
        hasher.update(x)
        hasher.update(b":")
        hasher.update(y)
    return sign_headers


def validate_signature_fields(sig, mandatory_fields=[b'v', b'a', b'b', b'bh', b'd', b'h', b's'], arc=False):
    """Validate DKIM or ARC Signature fields.
    Basic checks for presence and correct formatting of mandatory fields.
    Raises a ValidationError if checks fail, otherwise returns None.
    @param sig: A dict mapping field keys to values.
    @param mandatory_fields: A list of non-optional fields
    @param arc: flag to differentiate between dkim & arc
    """
    if arc:
        hashes = ARC_HASH_ALGORITHMS
    else:
        hashes = HASH_ALGORITHMS
    for field in mandatory_fields:
        if field not in sig:
            raise ValidationError("missing %s=" % field)

    if b'a' in sig and not sig[b'a'] in hashes:
        raise ValidationError("unknown signature algorithm: %s" % sig[b'a'])

    if b'b' in sig:
        if re.match(br"[\s0-9A-Za-z+/]+[\s=]*$", sig[b'b']) is None:
            raise ValidationError("b= value is not valid base64 (%s)" % sig[b'b'])
        if len(re.sub(br"\s+", b"", sig[b'b'])) % 4 != 0:
            raise ValidationError("b= value is not valid base64 (%s)" % sig[b'b'])

    if b'bh' in sig:
        if re.match(br"[\s0-9A-Za-z+/]+[\s=]*$", sig[b'b']) is None:
            raise ValidationError("bh= value is not valid base64 (%s)" % sig[b'bh'])
        if len(re.sub(br"\s+", b"", sig[b'bh'])) % 4 != 0:
            raise ValidationError("bh= value is not valid base64 (%s)" % sig[b'bh'])

    if b'cv' in sig and sig[b'cv'] not in (CV_Pass, CV_Fail, CV_None):
        raise ValidationError("cv= value is not valid (%s)" % sig[b'cv'])

    # Limit domain validation to ASCII domains because too hard
    try:
        str(sig[b'd'], 'ascii')
        # No specials, which is close enough
        if re.findall(rb"[\(\)<>\[\]:;@\\,]", sig[b'd']):
            raise ValidationError("d= value is not valid (%s)" % sig[b'd'])
    except UnicodeDecodeError as e:
        # Not an ASCII domain
        pass

    # Nasty hack to support both str and bytes... check for both the
    # character and integer values.
    if not arc and b'i' in sig and (
        not sig[b'i'].lower().endswith(sig[b'd'].lower()) or
        sig[b'i'][-len(sig[b'd'])-1] not in ('@', '.', 64, 46)):
        raise ValidationError(
            "i= domain is not a subdomain of d= (i=%s d=%s)" %
            (sig[b'i'], sig[b'd']))
    if b'l' in sig and re.match(br"\d{,76}$", sig[b'l']) is None:
        raise ValidationError(
            "l= value is not a decimal integer (%s)" % sig[b'l'])
    if b'q' in sig and sig[b'q'] != b"dns/txt":
        raise ValidationError("q= value is not dns/txt (%s)" % sig[b'q'])

    if b't' in sig:
        if re.match(br"\d+$", sig[b't']) is None:
            raise ValidationError(
                "t= value is not a decimal integer (%s)" % sig[b't'])
        # now = int(time.time())
        # slop = 36000 # 10H leeway for mailers with inaccurate clocks
        # t_sign = int(sig[b't'])
        # if t_sign > now + slop:
        #     raise ValidationError("t= value is in the future (%s)" % sig[b't'])

    if b'v' in sig and sig[b'v'] != b"1":
        raise ValidationError("v= value is not 1 (%s)" % sig[b'v'])

    if b'x' in sig:
        if re.match(br"\d+$", sig[b'x']) is None:
            raise ValidationError(
              "x= value is not a decimal integer (%s)" % sig[b'x'])
        # x_sign = int(sig[b'x'])
        # now = int(time.time())
        # slop = 36000 # 10H leeway for mailers with inaccurate clocks
        # if x_sign < now - slop:
        #     raise ValidationError(
        #         "x= value is past (%s)" % sig[b'x'])
        #     if x_sign < t_sign:
        #         raise ValidationError(
        #             "x= value is less than t= value (x=%s t=%s)" %
        #             (sig[b'x'], sig[b't']))


def rfc822_parse(message):
    """Parse a message in RFC822 format.

    @param message: The message in RFC822 format. Either CRLF or LF is an accepted line separator.
    @return: Returns a tuple of (headers, body) where headers is a list of (name, value) pairs.
    The body is a CRLF-separated string.
    """
    headers = []
    lines = re.split(b"\r?\n", message)
    i = 0
    while i < len(lines):
        if len(lines[i]) == 0:
            # End of headers, return what we have plus the body, excluding the blank line.
            i += 1
            break
        if lines[i][0] in ("\x09", "\x20", 0x09, 0x20):
            headers[-1][1] += lines[i]+b"\r\n"
        else:
            m = re.match(br"([\x21-\x7e]+?):", lines[i])
            if m is not None:
                headers.append([m.group(1), lines[i][m.end(0):]+b"\r\n"])
            elif lines[i].startswith(b"From "):
                pass
            else:
                raise MessageFormatError("Unexpected characters in RFC822 header: %s" % lines[i])
        i += 1
    return (headers, b"\r\n".join(lines[i:]))


#: Abstract base class for holding messages and options during DKIM/ARC signing and verification.
class DomainSigner(object):
  # NOTE - the first 2 indentation levels are 2 instead of 4
  # to minimize changed lines from the function only version.

  #: @param message: an RFC822 formatted message to be signed or verified
  #: (with either \\n or \\r\\n line endings)
  #: @param logger: a logger to which debug info will be written (default None)
  #: @param signature_algorithm: the signing algorithm to use when signing
  #: @param debug_content: log headers and body after canonicalization (default False)
  #: @param linesep: use this line seperator for folding the headers
  #: @param timeout: number of seconds for DNS lookup timeout (default = 5)
  #: @param tlsrpt: message is an RFC 8460 TLS report (default False)
  #: False: Not a tlsrpt, True: Is a tlsrpt, 'strict': tlsrpt, invalid if
  #: service type is missing. For signing, if True, length is never used.
  def __init__(self,message=None,logger=None,signature_algorithm=b'rsa-sha256',
        minkey=1024, linesep=b'\r\n', debug_content=False, timeout=5,
        tlsrpt=False):
    self.set_message(message)
    if logger is None:
        logger = get_default_logger()
    self.logger = logger
    self.debug_content = debug_content and logger.isEnabledFor(logging.DEBUG)
    if signature_algorithm not in HASH_ALGORITHMS:
        raise ParameterError(
            "Unsupported signature algorithm: "+signature_algorithm)
    self.signature_algorithm = signature_algorithm
    #: Header fields which should be signed.  Default as suggested by RFC6376
    self.should_sign = set(DKIM.SHOULD)
    #: Header fields which should not be signed.  The default is from RFC6376.
    #: Attempting to sign these headers results in an exception.
    #: If it is necessary to sign one of these, it must be removed
    #: from this list first.
    self.should_not_sign = set(DKIM.SHOULD_NOT)
    #: Header fields to sign an extra time to prevent additions.
    self.frozen_sign = set(DKIM.FROZEN)
    #: Minimum public key size.  Shorter keys raise KeyFormatError. The
    #: default is 1024
    self.minkey = minkey
    # use this line seperator for output
    self.linesep = linesep
    self.timeout = timeout
    self.tlsrpt = tlsrpt
    # Service type in DKIM record is s=tlsrpt
    self.seqtlsrpt = False


  #: Header fields to protect from additions by default.
  #:
  #: The short list below is the result more of instinct than logic.
  #: @since: 0.5
  FROZEN = (b'from',)

  #: The rfc6376 recommended header fields to sign
  #: @since: 0.5
  SHOULD = (
    b'from', b'sender', b'reply-to', b'subject', b'date', b'message-id', b'to', b'cc',
    b'mime-version', b'content-type', b'content-transfer-encoding',
    b'content-id', b'content-description', b'resent-date', b'resent-from',
    b'resent-sender', b'resent-to', b'resent-cc', b'resent-message-id',
    b'in-reply-to', b'references', b'list-id', b'list-help', b'list-unsubscribe',
    b'list-subscribe', b'list-post', b'list-owner', b'list-archive'
  )

  #: The rfc6376 recommended header fields not to sign.
  #: @since: 0.5
  SHOULD_NOT = (
    b'return-path',b'received',b'comments',b'keywords',b'bcc',b'resent-bcc',
    b'dkim-signature'
  )

  # Doesn't seem to be used (GS)
  #: The U{RFC5322<http://tools.ietf.org/html/rfc5322#section-3.6>}
  #: complete list of singleton headers (which should
  #: appear at most once).  This can be used for a "paranoid" or
  #: "strict" signing mode.
  #: Bcc in this list is in the SHOULD NOT sign list, the rest could
  #: be in the default FROZEN list, but that could also make signatures
  #: more fragile than necessary.
  #: @since: 0.5
  RFC5322_SINGLETON = (b'date',b'from',b'sender',b'reply-to',b'to',b'cc',b'bcc',
        b'message-id',b'in-reply-to',b'references')


  #: Load a new message to be signed or verified.
  #: @param message: an RFC822 formatted message to be signed or verified
  #: (with either \\n or \\r\\n line endings)
  #: @since: 0.5
  def set_message(self,message):
    if message:
      self.headers, self.body = rfc822_parse(message)
    else:
      self.headers, self.body = [],''
    #: The DKIM signing domain last signed or verified.
    self.domain = None
    #: The DKIM key selector last signed or verified.
    self.selector = 'default'
    #: Signature parameters of last sign or verify.  To parse
    #: a DKIM-Signature header field that you have in hand,
    #: use L{dkim.util.parse_tag_value}.
    self.signature_fields = {}
    #: The list of headers last signed or verified.  Each header
    #: is a name,value tuple.  FIXME: The headers are canonicalized.
    #: This could be more useful as original headers.
    self.signed_headers = []
    #: The public key size last verified.
    self.keysize = 0

  def verify_sig_process(self, sig, include_headers, sig_header, infoOut):
    """Non-async sensitive verify_sig elements.  Separated to avoid async code
    duplication."""
    # RFC 8460 MAY ignore signatures without tlsrpt Service Type
    if self.tlsrpt == 'strict' and not self.seqtlsrpt:
        raise ValidationError("Message is tlsrpt and Service Type is not tlsrpt")
    # Inferred requirement from both RFC 8460 and RFC 6376
    if not self.tlsrpt and self.seqtlsrpt:
        raise ValidationError("Message is not tlsrpt and Service Type is tlsrpt")

    try:
        canon_policy = CanonicalizationPolicy.from_c_value(sig.get(b'c', b'simple/simple'))
    except InvalidCanonicalizationPolicyError as e:
        raise MessageFormatError("invalid c= value: %s" % e.args[0])

    hasher = HASH_ALGORITHMS[sig[b'a']]

    # validate body if present
    if b'bh' in sig:
      h = HashThrough(hasher(), self.debug_content)

      body = canon_policy.canonicalize_body(self.body)
      if b'l' in sig and not self.tlsrpt:
        body = body[:int(sig[b'l'])]
      h.update(body)
    #   if self.debug_content:
    #       self.logger.debug("body hashed: %r" % h.hashed())
      bodyhash = h.digest()

      #self.logger.debug("bh: %s" % base64.b64encode(bodyhash))
      try:
          bh = base64.b64decode(re.sub(br"\s+", b"", sig[b'bh']))
      except TypeError as e:
          raise MessageFormatError(str(e))
      if bodyhash != bh:
        #   raise ValidationError(
        #       "body hash mismatch (got %s, expected %s)" %
        #       (base64.b64encode(bodyhash), sig[b'bh']))
        infoOut['body_hash_mismatch'] = True

    # address bug#644046 by including any additional From header
    # fields when verifying.  Since there should be only one From header,
    # this shouldn't break any legitimate messages.  This could be
    # generalized to check for extras of other singleton headers.
    if b'from' in include_headers:
      include_headers.append(b'from')
    h = HashThrough(hasher(), True)

    headers = canon_policy.canonicalize_headers(self.headers)
    self.signed_headers = hash_headers(
        h, canon_policy, headers, include_headers, sig_header, sig)
    # if self.debug_content:
    #     self.logger.debug("signed for %s: %r" % (sig_header[0], h.hashed()))
    # signature = base64.b64decode(re.sub(br"\s+", b"", sig[b'b']))
    infoOut['signed_data'] = h.hashed()
    # if self.ktag == b'rsa':
    #     try:
    #         res = RSASSA_PKCS1_v1_5_verify(h, signature, self.pk)
    #         self.logger.debug("%s valid: %s" % (sig_header[0], res))
    #         if res and self.keysize < self.minkey:
    #             raise KeyFormatError("public key too small: %d" % self.keysize)
    #         return res
    #     except (TypeError,DigestTooLargeError) as e:
    #         raise KeyFormatError("digest too large for modulus: %s"%e)
    # elif self.ktag == b'ed25519':
    #     try:
    #         self.pk.verify(h.digest(), signature)
    #         self.logger.debug("%s valid" % (sig_header[0]))
    #         return True
    #     except (nacl.exceptions.BadSignatureError) as e:
    #         return False
    # else:
    #     raise UnknownKeyTypeError(self.ktag)

#: Hold messages and options during DKIM signing and verification.
class DKIM(DomainSigner):

  def verify_headerprep(self, idx=0):
    """Non-DNS verify parts to minimize asyncio code duplication."""

    sigheaders = [(x,y) for x,y in self.headers if x.lower() == b"dkim-signature"]
    if len(sigheaders) <= idx:
        return False

    # By default, we validate the first DKIM-Signature line found.
    try:
        sig = parse_tag_value(sigheaders[idx][1])
        self.signature_fields = sig
    except InvalidTagValueList as e:
        raise MessageFormatError(e)

    #self.logger.debug("sig: %r" % sig)

    validate_signature_fields(sig)
    self.domain = sig[b'd']
    self.selector = sig[b's']

    include_headers = [x.lower() for x in re.split(br"\s*:\s*", sig[b'h'])]
    self.include_headers = tuple(include_headers)
    return sig, include_headers, sigheaders

  #: Verify a DKIM signature.
  #: @type idx: int
  #: @param idx: which signature to verify.  The first (topmost) signature is 0.
  #: @param dnsfunc: an option function to lookup TXT resource records
  #: for a DNS domain.  The default uses dnspython or pydns.
  #: @return: True if signature verifies or False otherwise
  #: @raise DKIMException: when the message, signature, or key are badly formed
  def verify(self,idx=0, infoOut=None):
    prep = self.verify_headerprep(idx)
    if prep:
        sig, include_headers, sigheaders = prep
        #return self.verify_sig(sig, include_headers, sigheaders[idx], dnsfunc, infoOut)
        return self.verify_sig_process(sig, include_headers, sigheaders[idx], infoOut)
    return False # No signature


