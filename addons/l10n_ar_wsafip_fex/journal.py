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
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)

class account_journal(osv.osv):


    #TODO: aqui deberia estar el _get_afip_items_generated para WSFEX. 
    def _get_afip_items_generated(self, cr, uid, ids, fields_name, arg, context=None):
        if context is None:
            context={}
        glin = lambda conn, ps, jc: conn.server_id.wsfex_get_last_invoice_number(conn.id, ps, jc)[conn.server_id.id]
        r={}
        for journal in self.browse(cr, uid, ids):
            r[journal.id] = False
            conn = journal.afip_connection_id
            if conn and conn.server_id.code == 'wsfex':
                try:
                    r[journal.id] = glin(conn, journal.point_of_sale, journal.journal_class_id.afip_code)
                except:
                    r[journal.id] = False
            _logger.debug("AFIP number of invoices in %s is %s" % (journal.name, r[journal.id]))
        return r
    
    _inherit = "account.journal"
    _columns = {
        'afip_items_generated': fields.function(_get_afip_items_generated, type='integer', string='Number of Invoices Generated',method=True, 
                            help="Connect to the AFIP and check how many invoices was generated.", readonly=True),
    }

account_journal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
