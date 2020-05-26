# This file exists within 'nark':
#
#   https://github.com/hotoffthehamster/nark
#
# Copyright © 2018-2020 Landon Bouma
# Copyright © 2015-2016 Eric Goller
# All  rights  reserved.
#
# 'nark' is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License  as  published by the Free Software Foundation,
# either version 3  of the License,  or  (at your option)  any   later    version.
#
# 'nark' is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY  or  FITNESS FOR A PARTICULAR
# PURPOSE.  See  the  GNU General Public License  for  more details.
#
# You can find the GNU General Public License reprinted in the file titled 'LICENSE',
# or visit <http://www.gnu.org/licenses/>.

import pytest


class TestCategoryManager():
    def test_add(self, basestore, category):
        with pytest.raises(NotImplementedError):
            basestore.categories._add(category)

    def test_update(self, basestore, category):
        with pytest.raises(NotImplementedError):
            basestore.categories._update(category)

    def test_remove(self, basestore, category):
        with pytest.raises(NotImplementedError):
            basestore.categories.remove(category)

    def test_get_invalid_pk(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.categories.get(12)

    def test_get_invalid_pk_type(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.categories.get_by_name('fooo')

    def test_save_wrong_type(self, basestore, category):
        with pytest.raises(TypeError):
            basestore.categories.save([])

    def test_save_new(self, basestore, category, mocker):
        """Make sure that saving an new category calls ``__add``."""
        basestore.categories._add = mocker.MagicMock(return_value=category)
        try:
            basestore.categories.save(category)
        except NotImplementedError:
            pass
        assert basestore.categories._add.called

    def test_save_existing(self, basestore, category, mocker):
        category.pk = 0
        basestore.categories._update = mocker.MagicMock(return_value=category)
        try:
            basestore.categories.save(category)
        except NotImplementedError:
            pass
        assert basestore.categories._update.called

    def test_get_or_create_existing(self, basestore, category, mocker):
        """Make sure the category is beeing looked up and no new one is created."""
        basestore.categories.get_by_name = mocker.MagicMock(return_value=category)
        basestore.categories._add = mocker.MagicMock(return_value=category)
        try:
            basestore.categories.get_or_create(category.name)
        except NotImplementedError:
            pass
        assert basestore.categories._add.called is False
        assert basestore.categories.get_by_name.called

    def test_get_or_create_new_category(self, basestore, category, mocker):
        """Make sure the category is beeing looked up and new one is created."""
        basestore.categories._add = mocker.MagicMock(return_value=category)
        basestore.categories.get_by_name = mocker.MagicMock(side_effect=KeyError)
        try:
            basestore.categories.get_or_create(category.name)
        except NotImplementedError:
            pass
        assert basestore.categories.get_by_name.called
        assert basestore.categories._add.called

    def test_get_all(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.categories.get_all()

