
.PHONY : update_vendor_assets

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

	# Done