import axios from "axios";

export async function upsert(domain: string, selector: string) {
	const upsertApiUrl = 'api/upsert_dkim_record';
	await axios.get(upsertApiUrl, { params: { domain, selector } })
		.then(response => {
			console.log('upsert response', response);
		}).catch(error => {
			console.error(error);
			let data = error?.response?.data;
			let message = `${error}` + (data ? ` - ${data}` : "");
			throw message;
		})
}