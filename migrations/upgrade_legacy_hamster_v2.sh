#!/bin/bash

# This file is part of 'hamster-lib'.
#
# 'hamster-lib' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'hamster-lib' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'hamster-lib'.  If not, see <http://www.gnu.org/licenses/>.

upgrade_legacy_db() {
  local db_path
  db_path=$1

  # Verify the target database exists.
  [[ -z ${db_path} ]] && echo "What's the path to your hamster.db?" && exit 1
  [[ ! -f ${db_path} ]] && echo "No such file at: ${db_path}" && exit 1

  # Find the upgrade script.
  local migrations_dir="$(dirname ${BASH_SOURCE[0]})"
  local upgrade_sql
  upgrade_sql=${migrations_dir}/upgrade_legacy_hamster_v2.sql
  [[ ! -f ${upgrade_sql} ]] && echo "Did not find SQL at: ${upgrade_sql}." && exit 1

  # Check the legacy version.
  db_version=$(echo "SELECT * FROM version;" | sqlite3 ${db_path})
  if [[ $? -ne 0 ]]; then
    echo "ERROR: Could not read from 'version' table. You figure it out."
    exit 1
  fi
  echo "Legacy DB Version: ${db_version}"

  if [[ ${db_version} != "9" ]]; then
    echo "ERROR: Expected Legacy DB Version \"9\", but found: ${db_version}"
    exit 1
  fi

  # Finally! We made it!!
  echo "Upgrading!"
  #local db_url
  #db_url=sqlite:///${db_path}
  #sqlite3 ${db_url} < ${upgrade_sql}
  sqlite3 ${db_path} < ${upgrade_sql}
}

main () {
  upgrade_legacy_db "$@"
}

main "$@"

