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
from suds.client import Client
import logging
import sys
from sslhttps import HttpsTransport

# logging.getLogger('suds.transport').setLevel(logging.DEBUG)

class wsafip_server(osv.osv):
    _name = "wsafip.server"
    _inherit = "wsafip.server"

    """
    Ref: http://www.afip.gob.ar/fe/documentos/WSFEX-Manualparaeldesarrollador_V1.pdf
    TODO:
        AFIP Description: Recupera los datos completos de un comprobante ya autorizado (FEXGetCMP)
        AFIP Description: Recupera la cotizacion de la moneda consultada y su fecha (FEXGetPARAM_Ctz)
        AFIP Description: Recupera el listado de paises (FEXGetPARAM_DST_pais)
    """

    def wsfex_get_status(self, cr, uid, ids, conn_id, context=None):
        """
        AFIP Description: Método Dummy para verificación de funcionamiento de infraestructura (FEXDummy)
        """
        conn_obj = self.pool.get('wsafip.connection')

        r = {}
        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if nescesary.

            try:
                _logger.debug('Query AFIP Web service status')
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                response = srvclient.service.FEXDummy()
            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s') % (e[0], e[1]))
            r[srv.id] = (response.AuthServer,
                         response.AppServer,
                         response.DbServer)
        return r

    def wsfex_update_languages(self, cr, uid, ids, conn_id, context=None):
        """
        Updates the list of available Languages.

        AFIP Description: Recupera el listado de los idiomas y sus codigos utilizables en servicio de autorizacion (FEXGetPARAM_Idiomas)
        """
        conn_obj = self.pool.get('wsafip.connection')

        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            # Take the connection, continue if connected or clockshifted
            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if necessary.
            if conn.state not in  [ 'connected', 'clockshifted' ]: continue

            # Build request
            try:
                _logger.debug('Updating list of Languages from AFIP Web service')
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                response = srvclient.service.FEXGetPARAM_Idiomas(Auth=conn.get_auth())

                # Take list of available languages
                languages_list = [
                    {'afip_lang_id': res.Idi_Id,
                     'language_name': res.Idi_Ds }
                    for res in response.FEXResultGet.ClsFEXResponse_Idi ]
            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s') % (e[0], e[1]))

            _update(self.pool, cr, uid,
                    'afip.fex_language',
                    languages_list,
                    can_create=True
                   )

        return

    def wsfex_update_incoterms(self, cr, uid, ids, conn_id, context=None):
        """
        Updates the list of available Incoterms.

        AFIP Description: Recupera el listado Incoterms utilizables en servicio de autorizacion (FEXGetPARAM_Incoterms)
        """
        conn_obj = self.pool.get('wsafip.connection')

        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            # Take the connection, continue if connected or clockshifted
            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if necessary.
            if conn.state not in  [ 'connected', 'clockshifted' ]: continue

            # Build request
            try:
                _logger.debug('Updating list of Incoterms from AFIP Web service')
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                response = srvclient.service.FEXGetPARAM_Incoterms(Auth=conn.get_auth())

                # Take list of available Incoterms
                incoterms_list = [
                    {'afip_incoterm_code': res.Inc_Id,
                     'incoterm_dsc': res.Inc_Ds }
                    for res in response.FEXResultGet.ClsFEXResponse_Inc ]
            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s') % (e[0], e[1]))

            _update(self.pool, cr, uid,
                    'afip.fex_incoterms',
                    incoterms_list,
                    can_create=True
                   )

        return

    def wsfex_update_currency(self, cr, uid, ids, conn_id, context=None):
        """
        Update currency. This function must be called from connection model.

        AFIP Description: Recupera el listado de monedas y su codigo utilizables en servicio de autorizacion (FEXGetPARAM_MON) 
        """
        conn_obj = self.pool.get('wsafip.connection')

        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            # Take the connection, continue if connected or clockshifted
            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if necessary.
            if conn.state not in  [ 'connected', 'clockshifted' ]: continue

            try:
                _logger.info('Updating currency from AFIP Web service')
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                response = srvclient.service.FEXGetPARAM_MON(Auth=conn.get_auth())

                # Take list of currency
                currency_list = [
                    { 'afip_code': c.Mon_Id,
                      'name': c.Mon_Ds }
                    for c in response.FEXResultGet.ClsFEXResponse_Mon
                ]
            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s') % (e[0], e[1]))

            _update(self.pool, cr, uid,
                    'res.currency',
                    currency_list,
                    can_create=False
                   )
        return True
        
    def wsfex_update_uom(self, cr, uid, ids, conn_id, context=None):
        """
        Update UoM. This function must be called from connection model.

        AFIP Description: Recupera el listado de las unidades de medida y su codigo utilizables en servicio de autorizacion (FEXGetPARAM_UMed) 
        """
        conn_obj = self.pool.get('wsafip.connection')

        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            # Take the connection, continue if connected or clockshifted
            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if necessary.
            if conn.state not in  [ 'connected', 'clockshifted' ]: continue

            try:
                _logger.info('Updating UoM from AFIP Web service')
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                response = srvclient.service.FEXGetPARAM_UMed(Auth=conn.get_auth())

                # Take list of UoM available
                uom_list = [
                    { 'afip_code': c.Umed_Id,
                      'name': c.Umed_Ds }
                    for c in response.FEXResultGet.ClsFEXResponse_UMed
                ]
            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s') % (e[0], e[1]))

            _update(self.pool, cr, uid,
                    'product.uom',
                    uom_list,
                    can_create=True
                   )
        return True

    def wsfex_get_last_invoice_number(self, cr, uid, ids, conn_id, ptoVta, cbteTipo, context=None):
        """
        Get last invoice number from AFIP

        AFIP Description: Recupera el ultimo comprobante autorizado (FEXGetLast_CMP)
        """
        conn_obj = self.pool.get('wsafip.connection')

        r={}

        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            # Take the connection
            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if necessary.
            if conn.state not in  [ 'connected', 'clockshifted' ]:
                r[srv.id] = False
                continue

            try:
                _logger.info('Take last invoice number from AFIP Web service')
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                response = srvclient.service.FEXGetLast_CMP(Auth=conn.get_auth(), PtoVta=ptoVta, CbteTipo=cbteTipo)

            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s\n'
                                       u'Pueda que esté intente realizar esta operación'
                                       u'desde el servidor de homologación.'
                                       u'Intente desde el servidor de producción.') % (e[0], e[1]))

            if hasattr(response, 'Errors'):
                for e in response.Errors.Err:
                    code = e.Code
                    _logger.error('AFIP Web service error!: (%i) %s' % (e.Code, e.Msg))
                r[srv.id] = False
            else:
                r[srv.id] = int(response.FEXGetLast_CMPResult.FEXResult_LastCMP.CbteNro)
        return r
        
    def wsfex_get_last_id(self, cr, uid, ids, conn_id, context=None):
        """
        Get Last ID number from AFIP.

        AFIP Description: Recupera el ultimo ID y su fecha (FEXGetLast_ID) 
        """
        conn_obj = self.pool.get('wsafip.connection')

        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            # Take the connection
            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if necessary.
            if conn.state not in  [ 'connected', 'clockshifted' ]:
                r[srv.id] = False
                continue

            try:
                _logger.info('Take last invoice number from AFIP Web service')
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                response = srvclient.service.FEXGetLast_ID(Auth=conn.get_auth())

            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s\n'
                                       u'Pueda que esté intente realizar esta operación'
                                       u'desde el servidor de homologación.'
                                       u'Intente desde el servidor de producción.') % (e[0], e[1]))

            if hasattr(response, 'Errors'):
                for e in response.Errors.Err:
                    code = e.Code
                    _logger.error('AFIP Web service error!: (%i) %s' % (e.Code, e.Msg))
                r[srv.id] = False
            else:
                r[srv.id] = int(response.FEXGetLast_IDResult.FEXResultGet.Id)
        return r
    
    def wsfex_check_permissions(client, token, sign, cuit, id_permiso, dst_merc):
        """
        Check shipment/destination country permissions from AFIP

        AFIP Description: Verifica la existencia de la permiso/pais de destinación de embarque ingresado (FEXCheck_Permiso)
        """
        conn_obj = self.pool.get('wsafip.connection')

        r={}

        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            # Take the connection
            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if necessary.
            if conn.state not in  [ 'connected', 'clockshifted' ]:
                r[srv.id] = False
                continue

            try:
                _logger.info('Check shipment/destination country permissions from AFIP Web service')
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                response = srvclient.service.FEXCheck_Permiso(Auth=conn.get_auth(), ID_Permiso=id_permiso, Dst_merc=dst_merc)

            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s\n'
                                       u'Pueda que esté intente realizar esta operación'
                                       u'desde el servidor de homologación.'
                                       u'Intente desde el servidor de producción.') % (e[0], e[1]))

            if hasattr(response, 'Errors'):
                for e in response.Errors.Err:
                    code = e.Code
                    _logger.error('AFIP Web service error!: (%i) %s' % (e.Code, e.Msg))
                r[srv.id] = False
            else:
                r[srv.id] = str(response.FEXCheck_PermisoResult.FEXResultGet.Status)
        return r
        
    def wsfex_get_cae(self, cr, uid, ids, conn_id, invoice_request, context=None):
        """
        Get CAE.

        AFIP Description: Autoriza un comprobante, devolviendo su CAE correspondiente (FEXAuthorize)
        """
        conn_obj = self.pool.get('wsafip.connection')
        r = {}

        for srv in self.browse(cr, uid, ids, context=context):
            # Ignore servers without code WSFEX.
            if srv.code != 'wsfex': continue

            # Take the connection
            conn = conn_obj.browse(cr, uid, conn_id, context=context) 
            conn.login() # Login if necessary.
            if conn.state not in  [ 'connected', 'clockshifted' ]: continue

            _logger.info('Get CAE from AFIP Web service')

            try:
                srvclient = Client(srv.url+'?WSDL', transport=HttpsTransport())
                first = invoice_request.keys()[0]
                response = srvclient.service.FEXAuthorize(Auth=conn.get_auth(),
                    Cmp = [dict([(k,v) for k,v in req.iteritems()]) for req in invoice_request.itervalues()]
                )
            except WebFault as e:
                #~ import pdb; pdb.set_trace()
                _logger.error('WebFault Error!: %s' % (e))
                raise osv.except_osv(_(u'WebFault Error!'),
                                     _(u'Error: %s') % (e))
            except Exception as e:
                _logger.error('AFIP Web service error!: (%i) %s' % (e[0], e[1]))
                raise osv.except_osv(_(u'AFIP Web service error'),
                                     _(u'System return error %i: %s') % (e[0], e[1]))

            for resp in response.FEXAuthorizeResult.FEXResultAuth:
                if resp.Resultado == 'R':
                    # Existe Error!
                    _logger.error('Rejected invoice: %s' % (resp,))
                    r[int(resp.Id)]={
                        'Eventos': [ (o.EventCode, unicode(o.EventMsg)) for o in response.FEXAuthorizeResult.FEXEvents ]
                                if hasattr(response.FEXAuthorizeResult, 'FEXEvents') else [],
                        'Errores': [ (e.ErrCode,   unicode(e.ErrMsg))   for e in response.FEXAuthorizeResult.FEXErr ]
                                if hasattr(response.FEXAuthorizeResult, 'FEXErr')    else [],
                    }
                else:
                    # Todo bien!
                    r[int(resp.Id)]={
                        'CAE': resp.Cae,
                        'CAEFchVto': resp.Fch_venc_Cae,
                    }
        return r


wsafip_server()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
