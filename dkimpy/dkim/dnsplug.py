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


__all__ = [
    'get_txt'
    ]


def get_txt_dnspython(name, timeout=5):
    """Return a TXT record associated with a DNS name."""
    import dkim
    try:
      a = dns.resolver.resolve(name, dns.rdatatype.TXT,raise_on_no_answer=False, lifetime=timeout, search=True)
      for r in a.response.answer:
          if r.rdtype == dns.rdatatype.TXT:
              return b"".join(list(r.items)[0].strings)
    except dns.resolver.NXDOMAIN: pass
    except dns.resolver.NoNameservers: pass
    except dns.resolver.NoResolverConfiguration as e:
        raise dkim.DnsTimeoutError('dns.resolver.NoResolverConfiguration: {0}'.format(e))
    except dns.exception.Timeout as e:
        raise dkim.DnsTimeoutError('dns.exception.Timeout: {0}'.format(e))
    return None


def get_txt_pydns(name, timeout=5):
    """Return a TXT record associated with a DNS name."""
    # Older pydns releases don't like a trailing dot.
    if name.endswith('.'):
        name = name[:-1]
    response = DNS.DnsRequest(name, qtype='txt', timeout=timeout).req()
    if not response.answers:
        return None
    for answer in response.answers:
        if answer['typename'].lower() == 'txt':
            return b''.join(answer['data'])
    return None


# No longer used since it doesn't support timeout
def get_txt_Milter_dns(name, timeout=5):
    """Return a TXT record associated with a DNS name."""
    # Older pydns releases don't like a trailing dot.
    if name.endswith('.'):
        name = name[:-1]
    sess = Session()
    a = sess.dns(name.encode('idna'),'TXT')
    if a: return b''.join(a[0])
    return None


# Prefer dnspython if it's there, otherwise use pydns.
try:
    import dns.resolver
    _get_txt = get_txt_dnspython
except ImportError:
    try:
        import DNS
        DNS.DiscoverNameServers()
        _get_txt = get_txt_pydns
    except:
        raise


def get_txt(name, timeout=5):
    """Return a TXT record associated with a DNS name.

    @param name: The bytestring domain name to look up.
    """
    # pydns needs Unicode, but DKIM's d= is ASCII (already punycoded).
    try:
        unicode_name = name.decode('UTF-8')
    except UnicodeDecodeError:
        return None
    txt = _get_txt(unicode_name, timeout)
    if type(txt) is str:
      txt = txt.encode('utf-8')
    return txt
