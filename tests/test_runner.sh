#!/bin/sh
# Simple script that runs linting and tests for drywall.
# Requires sudo, python3, flake8, pytest, postgresql.
#
# Usage: test_runner.sh [test/lint]
#	To run both linting and tests, leave empty

if [ ! -e config.json.sample ]; then
	echo "Please run the test runner from the directory you cloned drywall into!" >&2
	exit 1
fi

mode=all
do_test=""
do_lint=""
enable_coverage=""
no_db_setup=""
keep_db=""
copy_back_config=""

set_mode() {
	if [ $mode != all ]; then
		echo "Multiple modes have been provided!" >&2
		echo "Usage: test_runner.sh [test/lint]"
		echo "       To run both linting and tests, leave empty"
		exit 1
	fi
	mode=$1
}

for arg in $*; do
	case $arg in
		'test') set_mode test; do_test=true;;
		'lint') set_mode lint; do_lint=true;;
		'--no-db-setup') no_db_setup=true;; # don't perform DB setup operations
		'--enable-coverage') enable_coverage=true;; # enable codecov generation
		'--keep-test-db') keep_db=true;; # keep the test db created during test
	esac
done

if [ $mode = 'all' ]; then
	do_test=true
	do_lint=true
fi

set -e

if [ $do_lint ]; then
	echo -e "\033[33m[lint]\033[0m Checking for syntax errors..."
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82,F821 --show-source --statistics --use-flake8-tabs
	echo -e "\033[33m[lint]\033[0m No errors found. Linting as per usual..."
	# exit-zero treats all errors as warnings.
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --use-flake8-tabs --ignore=E302,E261,C901,E501,ET127,ET128
fi

if [ $do_test ]; then
	echo -e "\033[33m[test]\033[0m Running tests..."
	set -x
	## Set up test database
	# We use the names "drywall_testdb" and "drywall_test" to avoid conflicts
	# with existing databases

	if [ ! $no_db_setup ]; then
		sudo -Hu postgres psql <<- EOF
		DROP DATABASE IF EXISTS drywall_testdb;
		DROP USER IF EXISTS drywall_test;
		CREATE DATABASE drywall_testdb;
		CREATE USER drywall_test WITH PASSWORD 'drywall_test';
		GRANT ALL PRIVLEGES ON DATABASE drywall_testdb TO drywall_test;
		EOF
	fi

	## Create a config file with new database info
	if [ -e config.json ]; then
		mv config.json config.json.orig
		copy_back_config=true
	fi
	cp config.json.sample config.json
	sed -i 's/PostgreSQL database name/drywall_testdb/g' config.json
	sed -i 's/PostgreSQL user name/drywall_test/g' config.json
	sed -i 's/PostgreSQL user password/drywall_test/g' config.json

	if [ $enable_coverage ]; then
		coverage erase
	fi

	fail=''
	set +e
	if [ $enable_coverage ]; then
		coverage run -a --source=drywall -m pytest -vvv || fail=true
	else
		pytest -vvv || fail=true
	fi
	set -e

	if [ $fail ]; then
		echo -e "\n\033[31mTests failed.\033[0m\n"
	fi

	if [ $enable_coverage ]; then
		coverage xml
	fi

	if [ ! $no_db_setup ]; then
		if [ $keep_db ]; then
			echo -e '\033[33m!!! Keeping test database. !!!\033[0m'
		else
			sudo -Hu postgres psql <<- EOF
			DROP DATABASE IF EXISTS drywall_testdb;
			DROP USER IF EXISTS drywall_test;
			EOF
		fi
	fi

	if [ $copy_back_config ]; then
		mv config.json.orig config.json
	fi

	if [ $fail ]; then
		exit 1
	fi
fi

set +e
set +x

echo -e "\n\033[32mTests successful!\033[0m\n"

exit 0

