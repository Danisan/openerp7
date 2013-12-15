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
import re
import logging

_logger = logging.getLogger(__name__)

# Number Filter
re_number = re.compile(r'\d{8}')

def _calc_concept(product_types):
    if product_types == set(['consu']):
        concept = '1'
    elif product_types == set(['service']):
        concept = '2'
    elif product_types == set(['consu','service']):
        concept = '4'
    else:
        concept = False
    return concept

class invoice(osv.osv):

    def _get_concept(self, cr, uid, ids, name, args, context=None):
        r = {}
        for inv in self.browse(cr, uid, ids):
            concept = False
            product_types = set([ line.product_id.type for line in inv.invoice_line ])
            r[inv.id] = _calc_concept(product_types)
        return r

    _inherit = "account.invoice"
    _columns = {
    }

    _defaults = {
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'state':'draft',
            'afip_error_id': False,
            'afip_batch_number': False,
            'afip_cae_due': False,
            'afip_cae': False,
            'afip_result': False,
            'date_invoice': default.get('date_invoice', False),
            'date_due': default.get('date_due', False)
        })
        return super(invoice, self).copy(cr, uid, id, default, context)

    def action_retrieve_cae(self, cr, uid, ids, context=None):
        
        """
        Contact to the AFIP to get a CAE number.
        """
        if context is None:
            context = {}
        #TODO: not correct fix but required a frech values before reading it.
        self.write(cr, uid, ids, {})

        conn_obj = self.pool.get('wsafip.connection')
        serv_obj = self.pool.get('wsafip.server')
        currency_obj = self.pool.get('res.currency')

        Servers = {}
        Requests = {}
        Inv2id = {}
        for inv in self.browse(cr, uid, ids, context=context):
            journal = inv.journal_id
            conn = journal.afip_connection_id

            # Only process if set to connect to afip
            if not conn: continue
            
            # Ignore invoice if connection server is not type WSFEX.
            if conn.server_id.code != 'wsfex': continue

            Servers[conn.id] = conn.server_id.id

            # Take the last number of the "number".
            # Could not work if your number have not 8 digits.
            invoice_number = int(re_number.search(inv.number).group())

            _f_date = lambda d: d and d.replace('-','')

            # Build request dictionary
            if conn.id not in Requests: Requests[conn.id] = {}
            Requests[conn.id][inv.id]=dict( (k,v) for k,v in {
                'Id': journal.point_of_sale, ######## EDIT (AVERIGUAR ID)
                'CbteFch': _f_date(inv.date_invoice),
                'CbteTipo': journal.journal_class_id.afip_code,
                'PtoVta': journal.point_of_sale,
                'CbteNro': journal.point_of_sale, ########## BUSCAR NUMERO (00000103 por ej)
                'TipoExpo': inv.afip_concept, ############## EDITAR PARA QUE SEA TIPO_EXPO DIFERENTE AL DE LA WSFE
                
                'Permisos': { 'Permiso': self.get_permiso(cr, uid, inv.id) },
                
                'DstCmp': inv.partner_id.country_id.afip_code,
                'Cliente': inv.partner_id.name,
                'CuitPaisCliente': inv.partner_id.country_id.cuit_juridica if inv.partner_id.is_company == True else inv.partner_id.country_id.cuit_fisica,
                'DomicilioCliente': inv.partner_id.street+", "+inv.partner_id.city,
                'IdImpositivo': ######### AVERIGUAR COMO COMPLETAR ESTE CAMPO
                
                'MonId': inv.currency_id.afip_code,
                'MonCotiz': currency_obj.compute(cr, uid, inv.currency_id.id, inv.company_id.currency_id.id, 1.),
                
                'ObsComerciales': inv.comment, ####### NECESARIO HACER UN CAMPO NUEVO LLAMADO OBS COMERCIALES?
                'ImpTotal': inv.amount_total,
                'Obs': inv.comment,
                
                'CbtesAsoc': {'CbteAsoc': self.get_related_invoices(cr, uid, inv.id) },
                
                'FormaPago': inv.payment_term,
                'Incoterms': inv.payment_term, ####### HACER FUNCIONALIDAD DE INCOTERMS
                'IncotermsDs': inv.payment_term, ####### HACER FUNCIONALIDAD DE INCOTERMS DESCRIPTION (VACIO WHEN Incoterms == None)
                'IdiomaCbte': inv.payment_term, ####### HACER FUNCIONALIDAD IDIOMAS (son solo 3, necesario hacer una tabla?)
                
                'Items': { 'Item': self.get_item(cr, uid, inv.id) }, ####### HACER FUNCIONALIDAD ITEMS
                
            }.iteritems() if v is not None)
            Inv2id[invoice_number] = inv.id

        for c_id, req in Requests.iteritems():
            conn = conn_obj.browse(cr, uid, c_id)
            res = serv_obj.wsfex_get_cae(cr, uid, [conn.server_id.id], c_id, req) # TODO:
            for k, v in res.iteritems():
                if 'CAE' in v:
                    self.write(cr, uid, Inv2id[k], {
                        'afip_cae': v['CAE'],
                        'afip_cae_due': v['CAEFchVto'],
                    })
                else:
                    msg = 'Factura %s:\n' % k + '\n'.join(
                        [ u'(%s) %s\n' % e for e in v['Errores']] +
                        [ u'(%s) %s\n' % e for e in v['Eventos']]
                    )
                    raise osv.except_osv(_(u'AFIP Validation Error'), msg)

        return super(invoice, self).action_retrieve_cae(cr, uid, ids, context)

invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
