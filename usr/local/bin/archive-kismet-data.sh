#!/bin/bash

readonly TAG=$(date -Is --utc)
readonly BACKUP_DESTDIR=/var/log/archive
readonly BACKUP_TARBALL="$BACKUP_DESTDIR/kismet-$TAG.tar.xz"
readonly ARCHIVE_DIRS="/var/log/kismet/whitestar*"

echo "Archiving logs from '$ARCHIVE_DIRS' to '$BACKUP_TARBALL'"


# Reference: http://www.alecjacobson.com/weblog/?p=141
# Some changes to make it print the longest common prefix instead of removing it
common_prefix() {
	if [ "$#" -gt 0 ]; then
		input=$(echo “$@”)
	else
		input=$(cat)
	fi
	longest=$(echo "$input" | wc -L)
	count=$(echo "$input" | wc -l)
	prefix=1
	if [ $count -gt 1 ]; then
		for i in $(seq $longest); do
			[ $(echo "$input" | uniq -w$i | wc -l) -eq 1 ] || break
			prefix=$(($prefix+1))
		done
	fi
	echo "$input" | head -n 1 | cut -c-$(($prefix-1))
}


get_exclude_pattern() {
	# Exclude list of currently open files
	echo "$(lsof +d /var/log/kismet/ | awk '!/NAME/ { print $9; }' | common_prefix)*"
}

# Kill the spurious 'file changes as we read it' message on /var/log/kismet
# Reference: http://stackoverflow.com/questions/20318852/tar-file-changed-as-we-read-it#24012292
exclude_pattern=$(get_exclude_pattern)
tar --remove-files --warning=no-file-changed --force-local -Jcf "$BACKUP_TARBALL" ${exclude_pattern:+--exclude=${exclude_pattern}} $ARCHIVE_DIRS
