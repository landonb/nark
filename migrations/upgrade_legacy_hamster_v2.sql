/* This file is part of 'hamster-lib'.
 *
 * 'hamster-lib' is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * 'hamster-lib' is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with 'hamster-lib'.  If not, see <http://www.gnu.org/licenses/>.
 */

/* Because SQLite3 does not support ALTER TABLE ... DROP COLUMN. */

BEGIN TRANSACTION;

ALTER TABLE activities RENAME TO temp_activities;
ALTER TABLE categories RENAME TO temp_categories;
ALTER TABLE tags RENAME TO temp_tags;
ALTER TABLE facts RENAME TO temp_facts;
ALTER TABLE fact_tags RENAME TO temp_fact_tags;

/* NOTE: The CREATE TABLE statements is simply from a
        ``.schema`` command run against a new DB created
        by simply running ``hamster -v``.
*/

/* Drop columns from categories:
        color_code varchar2(50)     # empty ((lb): at least in my legacy db)
        category_order integer      # empty ((lb): at least in my legacy db)
        search_name varchar2        # simply, name.lower()
*/
CREATE TABLE categories (
	id INTEGER NOT NULL,
	name VARCHAR(254),
	PRIMARY KEY (id),
	UNIQUE (name)
);

/* Drop columns from activities:
        work integer                # empty ((lb): at least in my legacy db)
        activity_order integer      # empty ((lb): at least in my legacy db)
        search_name varchar2        # simply, name.lower()
*/
CREATE TABLE activities (
	id INTEGER NOT NULL,
	name VARCHAR(500),
	deleted BOOLEAN,
	category_id INTEGER,
	PRIMARY KEY (id),
	UNIQUE (name, category_id),
	CHECK (deleted IN (0, 1)),
	FOREIGN KEY(category_id) REFERENCES categories (id)
);

/* Drop columns from tags:
        autocomplete BOOL DEFAULT true  # (lb): I think this is the list the
                                        # legacy ``hamster-indicator`` app
                                        # let you edit in the interface.
                                        # This'll be replaced by ``hidden``.
*/
CREATE TABLE tags (
	id INTEGER NOT NULL,
	name VARCHAR(254),
	PRIMARY KEY (id),
	UNIQUE (name)
);

CREATE TABLE facts (
	id INTEGER NOT NULL,
	start_time DATETIME,
	end_time DATETIME,
	activity_id INTEGER,
	description VARCHAR(500),
	PRIMARY KEY (id),
	FOREIGN KEY(activity_id) REFERENCES activities (id)
);
CREATE TABLE fact_tags (
	fact_id INTEGER,
	tag_id INTEGER,
	FOREIGN KEY(fact_id) REFERENCES facts (id),
	FOREIGN KEY(tag_id) REFERENCES tags (id)
);

INSERT INTO activities
SELECT
    id, name, deleted, category_id
FROM
    temp_activities;

INSERT INTO categories
SELECT
    id, name
FROM
    temp_categories;

INSERT INTO tags
SELECT
    id, name
FROM
    temp_tags;

INSERT INTO facts
SELECT
    id, start_time, end_time, activity_id, description
FROM
    temp_facts;

INSERT INTO fact_tags
SELECT
    fact_id, tag_id
FROM
    temp_fact_tags;

DROP TABLE temp_fact_tags;
DROP TABLE temp_facts;
DROP TABLE temp_tags;
DROP TABLE temp_categories;
DROP TABLE temp_activities;

/* Other legacy stuff to drop. */

/* (lb): Had one row, with one cell (version integer), set to "9".
        CREATE TABLE version(version integer);
*/
DROP TABLE version;

/* (lb): I'm not sure what this *virtual* table was for. It runs functions.

    From hamster-applet/src/hamster/db.py:

    def run_fixtures(self):
        ...
        if version < 9:
            # adding full text search
            self.execute("""
                CREATE VIRTUAL TABLE fact_index
                USING fts3(id, name, category, description, tag)""")

    See:

    https://www.sqlite.org/fts3.html

    NOTE: Dropping fact_index automatically drops three related tables:

            fact_index_content
            fact_index_segments
            fact_index_segdir

*/
DROP TABLE fact_index;

COMMIT;

