# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Julius Network Solutions SARL <contact@julius.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from openerp.osv import fields, orm
from openerp.addons.tr_barcode.tr_barcode import _get_code

class tr_barcode_settings(orm.TransientModel):
    _inherit = 'tr.barcode.settings'
    
    def _get_default_product_config_id(self, cr, uid, context=None):
        config_obj = self.pool.get('tr.barcode.config')
        md_obj = self.pool.get('ir.model.data')
        model_id, res_id = md_obj.get_object_reference(cr, uid, 'product', 'model_product_product')
        res = config_obj.search(cr, uid, [('res_model', '=', res_id)], limit=1, context=context)
        return res and res[0] or False
    
    _columns = {
        'product_config_id': fields.many2one('tr.barcode.config', 'Production lot Config'),
        'product_model_id': fields.related('product_config_id', 'res_model', type='many2one', relation="ir.model", string="Model"),
        'product_field_id': fields.related('product_config_id', 'field', type='many2one', relation="ir.model.fields", string="Field"),
        'product_width': fields.related('product_config_id', 'width', type='integer', string="Width",
                help="Leave Blank or 0(ZERO) for default size"),
        'product_height': fields.related('product_config_id', 'height', type='integer', string="Height",
                help="Leave Blank or 0(ZERO) for default size"),
        'product_hr_form': fields.related('product_config_id', 'hr_form', type='boolean', string="Human Readable",
                help="To generate Barcode In Human readable form"),
        'product_barcode_type': fields.related('product_config_id', 'barcode_type', type='selection', selection=_get_code, string="Field"),
    }
    
    _defaults = {
        'product_config_id': _get_default_product_config_id,
    }
    
    def onchange_product_config_id(self, cr, uid, ids, product_config_id, context=None):
        values = {}
        if product_config_id:
            product_config = self.pool.get('tr.barcode.config').browse(cr, uid, product_config_id, context=context)
            values.update({
                'product_model_id': product_config.res_model and product_config.res_model.id or False,
                'product_field_id': product_config.field and product_config.field.id or False,
                'product_width': product_config.width or 0,
                'product_height': product_config.height or 0,
                'product_hr_form': product_config.hr_form or False,
                'product_barcode_type': product_config.barcode_type or False,
            })
        return {'value': values}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: