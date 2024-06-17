import * as fs from 'fs';
import { execFileSync } from "node:child_process";

function load_certificates(filename: string): string[] {
	// Extract pem certificates from ldif file
	const fileContent = fs.readFileSync(filename, "utf-8");
	const regex = /userCertificate;binary::\s*([\s\S]*?)(?=\w+:|\n\n|$)/g;
	let match: RegExpExecArray | null;

	const certificates: string[] = [];

	while ((match = regex.exec(fileContent)) !== null) {
		const certificate = match[1].replace(/\s+/g, "");
		certificates.push(`-----BEGIN CERTIFICATE-----\n${certificate}\n-----END CERTIFICATE-----\n`);
		break
	}
	return certificates;
}


function extractData(regex: RegExp, text: string): string | null {
	const match = text.match(regex);
	return match ? match[1].trim().replace(/\n/g, '') : null;
}

function hexToDecimal(hexString: string): string {
	return BigInt("0x" + hexString.replace(/[\n: ]/g, '')).toString();
}


function parseRsa(certText: string, signatureAlgorithm: string) {
	const modulusRegex = /Modulus:\s+([0-9a-f:\s]+?)\s+Exponent:/;
	const exponentRegex = /Exponent:\s+(\d+)/;

	const modulusMatch = certText.match(modulusRegex);
	const exponentMatch = certText.match(exponentRegex);

	const modulusHex = modulusMatch ? modulusMatch[1].replace(/[\s:]/g, '') : '';
	const exponent = exponentMatch ? exponentMatch[1] : '';

	if (!modulusHex) {
		console.error(`Modulus not found`);
		return null;
	}

	if (Number(exponent) !== 65537) {
		console.error(`signatureAlgorithm`, signatureAlgorithm, `exponent`, exponent);
		return null;
	}
	return {
		modulus: BigInt('0x' + modulusHex).toString(),
		exponent: exponent
	};
}

function parseEcdsa(certText: string, signatureAlgorithm: string) {
	const publicKeyAlgorithmRegex = /Public Key Algorithm: ([^\n]+)/;
	const publicKeyBitRegex = /Public-Key: \((\d+) bit\)/;
	const pubRegex = /pub:\n([0-9A-Fa-f:\n ]+?)\n\s{4}/;
	const fieldTypeRegex = /Field Type: ([^\n]+)/;
	const primeRegex = /Prime:\n([0-9A-Fa-f:\n ]+?)\n\s{4}/;
	const aRegex = /A:\s+\n([0-9A-Fa-f:\n ]+?)\n\s{4}/;
	const bRegex = /B:\s+\n([0-9A-Fa-f:\n ]+?)\n\s{4}/;
	const generatorRegex = /Generator \(uncompressed\):\n([0-9A-Fa-f:\n ]+?)\n\s{4}/;
	const orderRegex = /Order: \n([0-9A-Fa-f:\n ]+?)\n\s{4}/;
	const cofactorRegex = /Cofactor:\s+(\d+)/;

	// Extracting fields
	const publicKeyAlgorithm = extractData(publicKeyAlgorithmRegex, certText);
	const publicKeyBit = extractData(publicKeyBitRegex, certText);
	const pub = extractData(pubRegex, certText);
	const fieldType = extractData(fieldTypeRegex, certText);
	const prime = extractData(primeRegex, certText);
	const a = extractData(aRegex, certText);
	const b = extractData(bRegex, certText);
	const generator = extractData(generatorRegex, certText);
	const order = extractData(orderRegex, certText);
	const cofactor = extractData(cofactorRegex, certText);

	if (!prime) {
		console.error(`Prime not found`);
		return null;
	}

	return {
		publicKeyAlgorithm: publicKeyAlgorithm,
		publicKeyBit: publicKeyBit,
		pub: hexToDecimal(pub as string),
		fieldType: fieldType,
		prime: hexToDecimal(prime as string),
		a: hexToDecimal(a as string),
		b: hexToDecimal(b as string),
		generator: hexToDecimal(generator as string),
		order: hexToDecimal(order as string),
		cofactor: cofactor,
	};
}


function parsePubkey(certText: string, signatureAlgorithm: string) {
	if (signatureAlgorithm.includes("sha256WithRSAEncryption")
		|| signatureAlgorithm.includes("rsassaPss")
		|| signatureAlgorithm.includes("sha1WithRSAEncryption")
		|| signatureAlgorithm.includes("sha512WithRSAEncryption")
	) {
		return parseRsa(certText, signatureAlgorithm);
	}
	else if (signatureAlgorithm.includes("ecdsa-with-SHA1")
		|| signatureAlgorithm.includes("ecdsa-with-SHA384")
		|| signatureAlgorithm.includes("ecdsa-with-SHA256")
		|| signatureAlgorithm.includes("ecdsa-with-SHA512")
	) {
		return parseEcdsa(certText, signatureAlgorithm);
	};
}

async function parse_pem(data: string) {
	const args = ["x509", "-text", "-dateopt", "iso_8601", "-noout", '-modulus', '-pubkey', '-issuer', '-subject', '-serial', '-nameopt', 'oneline'];
	console.log(`running openssl ${args.join(" ")}`);
	const certText = execFileSync("openssl", args, { input: data }).toString('utf-8');;
	console.log(certText);

	const signatureAlgorithm = (certText.match(/Signature Algorithm: (.*)/) as RegExpExecArray)[1].trim();
	const issuerRegex = /Issuer: ([^\n]+)/;
	const issuer = extractData(issuerRegex, certText);
	const pubkey = parsePubkey(certText, signatureAlgorithm);
	if (!pubkey) {
		throw new Error(`Error parsing pubkey`);
	}
	return { signatureAlgorithm, issuer, ...pubkey }
}

async function main() {
	const certificates = load_certificates(process.argv[2]);
	for (const certificate of certificates) {
		let parseResult = await parse_pem(certificate);
		console.log(parseResult);
		break;
	}
}

main();
