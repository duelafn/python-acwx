# Author: Dean Serenevy  <dean@serenevy.net>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

COPYRIGHT_IGNORES = grep -vE '\.gitignore|Makefile|MANIFEST\.in|LICENSE|README|TODO|\.json|debian/|__init__|pylint\.conf|pep8\.ignore'

# Python
#-------
PKGNAME = amethyst
PKG_VERSION = $(shell perl -ne 'print $$1 if /^__version__\s*=\s*"([\d.]+(?:[\-\+~.]\w+)*)"/' amethyst/__init__.py)


.PHONY: all sdist dist debbuild clean test


all: test

zip: test
	python setup.py sdist --format=zip

sdist: test
	python setup.py sdist

dist: test debbuild
	mv -f debbuild/${PKGNAME}_* debbuild/python-${PKGNAME}_* dist/
	rm -rf debbuild

debbuild: sdist
	rm -rf debbuild
	mkdir -p debbuild
	grep "(${PKG_VERSION}-1)" debian/changelog || (echo "** debian/changelog requires update **" && false)
	mv -f dist/${PKGNAME}-${PKG_VERSION}.tar.gz debbuild/${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cd debbuild && tar -xzf ${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cp -r debian debbuild/${PKGNAME}-${PKG_VERSION}/
	cd debbuild/${PKGNAME}-${PKG_VERSION} && dpkg-buildpackage -rfakeroot -uc -us -tc -i

test:
	unit2 discover -s test
	@for f in $$(git grep -iIL copyright | ${COPYRIGHT_IGNORES}); do echo -e "\e[91mMissing Copyright Notice: $$f\e[0m"; done
	@for f in $$(git grep -iIL 'This program is free software' | ${COPYRIGHT_IGNORES}); do echo -e "\e[91mMissing LGPL notice: $$f\e[0m"; done
	@for f in $$(git grep -iIl 'rights reserved' | grep -v Makefile); do echo -e "\e[91mAll Rights Reserved: $$f\e[0m"; done

clean:
	pyclean .
	rm -rf build dist
	rm -f MANIFEST
