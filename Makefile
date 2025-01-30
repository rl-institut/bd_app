
.PHONY : update_vendor_assets, compile_dependencies, load_data

DJANGO_READ_DOT_ENV_FILE=True
export

load_data:
	python manage.py shell --command="from building_dialouge_webapp import setup; setup.load_profiles()"

DJANGO_READ_DOT_ENV_FILE=True
export

celery:
	redis-server --port 6379 & celery -A config.celery_app worker -l INFO

compile_dependencies:
	uv pip compile -q requirements/base.in -o requirements/base.txt
	uv pip compile -q requirements/local.in -o requirements/local.txt
	uv pip compile -q requirements/production.in -o requirements/production.txt

update_vendor_assets:
	# Note: call this command from the same folder your Makefile is located
	# Note: this run only update minor versions.
	# Update major versions manually, you can use "ncu" for this.
	# https://nodejs.dev/en/learn/update-all-the-nodejs-dependencies-to-their-latest-version/#update-all-packages-to-the-latest-version

	# Update
	npm update

	# Bootstrap https://github.com/twbs/bootstrap
	rm -r building_dialouge_webapp/static/vendors/bootstrap/scss/*
	cp -r node_modules/bootstrap/scss/* building_dialouge_webapp/static/vendors/bootstrap/scss/
	rm -r building_dialouge_webapp/static/vendors/bootstrap/js/*
	cp node_modules/bootstrap/dist/js/bootstrap.min.js* building_dialouge_webapp/static/vendors/bootstrap/js/

	# HTMX https://htmx.org/
	rm -r building_dialouge_webapp/static/vendors/htmx/js/*
	cp node_modules/htmx.org/dist/htmx.min.js building_dialouge_webapp/static/vendors/htmx/js/

	# eCharts https://echarts.apache.org/en/index.html
	rm -r building_dialouge_webapp/static/vendors/echarts/js/*
	cp node_modules/echarts/dist/echarts.min.js building_dialouge_webapp/static/vendors/echarts/js/

	# Done
