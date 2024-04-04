cd $(dirname $0)
cat dkimscan.pl.txt selector_frequencies_gt1.txt dkim_selectors.lst | sort | uniq > merged.txt
