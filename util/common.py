class DecodeTvlException(Exception):
	pass


def decode_dkim_tag_value_list(dkimData: str):
	# decode a DKIM Tag=Value list such as "v=1; a=rsa-sha256; d=example.net; s=brisbane;"
	# to a dictionary such as {'v': '1', 'a': 'rsa-sha256', 'd': 'example.net', 's': 'brisbane'}
	# See https://datatracker.ietf.org/doc/html/rfc6376#section-3.2

	tagValuePairStrings = list(map(lambda x: x.strip(), dkimData.split(';')))
	res: dict[str, str] = {}
	for s in tagValuePairStrings:
		if not s:
			continue
		try:
			key, value = s.split('=', 1)
		except ValueError:
			raise DecodeTvlException(f'Error decoding DKIM tag-value pair: {s}')
		key = key.strip()
		value = value.strip()
		res[key] = value
	return res
