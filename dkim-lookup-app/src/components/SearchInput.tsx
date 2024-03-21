"use client";
import { AutocompleteResults, autocomplete } from "@/app/actions";
import { Autocomplete, TextField } from "@mui/material";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface SearchFormProps {
	domainQuery: string | undefined;
}

export const SearchInput: React.FC<SearchFormProps> = ({ domainQuery }) => {
	const router = useRouter();
	const [searchResults, setSearchResults] = useState<AutocompleteResults>([]);

	function inputChanged(_event: React.SyntheticEvent, value: string) {
		autocomplete(value).then(results => setSearchResults(results));
	}

	function onChange(_event: React.SyntheticEvent, value: string | null) {
		if (value) {
			router.push(`/?domain=${value}`)
		}
	}

	return (
		<div>
			<Autocomplete
				style={{ margin: '1rem', backgroundColor: 'white' }}
				disablePortal
				onInputChange={inputChanged}
				onChange={onChange}
				options={searchResults}
				sx={{ width: 300 }}
				freeSolo
				renderInput={(params) => <TextField {...params} label="Domain name" />}
			/>
		</div>
	);
};
