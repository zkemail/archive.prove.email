def decode_dkim_header_field(dkimData: str):
	# decode a DKIM-Signature header field such as "v=1; a=rsa-sha256; d=example.net; s=brisbane;"
	# to a dictionary such as {'v': '1', 'a': 'rsa-sha256', 'd': 'example.net', 's': 'brisbane'}
	tagValuePairStrings = list(map(lambda x: x.strip(), dkimData.split(';')))
	res: dict[str, str] = {}
	for s in tagValuePairStrings:
		if not s:
			continue
		key, value = s.split('=', 1)
		key = key.strip()
		value = value.strip()
		res[key] = value
	return res

