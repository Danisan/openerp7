# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2012 OpenERP - Team de Localización Argentina.
# https://launchpad.net/~openerp-l10n-ar-localization
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{   'active': False,
    'author': 'OpenERP - Team de Localizaci\xc3\xb3n Argentina',
    'category': 'Localization/Argentina',
    'demo_xml': [],
    'depends': ['l10n_ar_wsafip_fe'],
    'description': '\n\nAPI e GUI para acceder a las Web Services de Factura Electr\xc3\xb3nica de Exportaci\xc3\xb3n de la AFIP\n\n',
    'init_xml': [],
    'installable': True,
    'license': 'AGPL-3',
    'name': 'Argentina - Web Services de Factura Electr\xc3\xb3nica del AFIP',
    'test': [   'test/test_key.yml',
                'test/partners.yml',
                'test/products.yml',
                'test/com_ri1.yml',
                'test/com_ri2.yml',
                'test/com_rm1.yml',
                'test/journal.yml',
                'test/invoice.yml',
                'test/inv_2prod.yml',
                'test/inv_2iva.yml'],
    'update_xml': [   'data/wsafip_server.xml',
                      'security/wsafip_fex_security.xml',
                      'security/ir.model.access.csv'],
    'version': '2.7.232',
    'website': 'https://launchpad.net/~openerp-l10n-ar-localization'}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
