# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Netquatro C.A. (http://openerp.netquatro.com/) All Rights Reserved.
#                    Javier Duran <javier.duran@netquatro.com>
# 
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields,osv
from tools.sql import drop_view_if_exists
import time
import datetime
from mx.DateTime import *
from tools import config


class report_profit_picking(osv.osv):
    def _get_invoice_line(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        aml_obj = self.pool.get('account.move.line')
        purchase_obj = self.pool.get('purchase.order')
        sale_obj = self.pool.get('sale.order')
        il_obj = self.pool.get('account.invoice.line')
        loc_obj = self.pool.get('stock.location')
        
        for rpp in self.browse(cr, uid, ids, context):
            result[rpp.id] = ()
            il_ids = []
            if rpp.purchase_line_id and rpp.purchase_line_id.id:                
                if rpp.purchase_line_id.order_id.invoice_id and \
                    rpp.purchase_line_id.order_id.invoice_id.id:
                    inv_id = rpp.purchase_line_id.order_id.invoice_id.id
                    il_ids = il_obj.search(cr, uid, [('invoice_id', '=', inv_id), ('product_id', '=', rpp.product_id.id), ('quantity', '=', rpp.picking_qty)])
            if rpp.sale_line_id and rpp.sale_line_id.id:
                cust_loc_ids = loc_obj.search(cr, uid, [('name', '=', 'Customers')])
                #cust_loc_ids = [8]
                lst_inv = []
                str_inv = ''
                inv_type ='out_invoice'
                if not cust_loc_ids:
                    raise osv.except_osv('Error', 'No hay una ubicacion cliente definida')
                               
                if rpp.sale_line_id.order_id.invoice_ids:
                    for inv in rpp.sale_line_id.order_id.invoice_ids:
                        if inv.id not in lst_inv:
                            lst_inv.append(inv.id)
                        if inv.child_ids:
                            for inv_nc in inv.child_ids:
                                if inv_nc.id not in lst_inv:
                                    lst_inv.append(inv_nc.id)
                                    
                    if lst_inv:
                        str_inv = ','.join(map(str, lst_inv))
                        #NC VENTA 
                        if rpp.location_id.id == cust_loc_ids[0]:
                            inv_type ='out_refund'
                        sql = '''
                            select
                                l.id as id
                            from account_invoice_line l
                                inner join account_invoice i on (i.id=l.invoice_id)
                            where i.id in (%s)  and i.type='%s' and l.product_id=%s and l.quantity=%s
''' % (str_inv,inv_type,rpp.product_id.id,rpp.picking_qty)
                        cr.execute(sql)
                        il_ids = [x[0] for x in cr.fetchall()]

            if il_ids:
                il = il_obj.browse(cr, uid, il_ids[0], context)
#                print 'lineas consultaxxx: ',il
                result[rpp.id] = (il.id,il.name)
            
        return result

    def _get_aml_cost(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        aml_obj = self.pool.get('account.move.line')
        for rpp in self.browse(cr, uid, ids, context):
            result[rpp.id] = ()
            if rpp.invoice_line_id and rpp.invoice_line_id.id:
                #print 'lf: ',rpp.invoice_line_id.id
                moves = self.aml_cost_get(cr, uid, [rpp.invoice_line_id.id])
            #677= llamo get_move_line
            #aml_query = aml_obj.find(cr, uid, mov_id=677)
            #print 'consultaxxx: ',aml_query
            #aml = aml_obj.browse(cr, uid, aml_query[0], context)
                if moves:
                    aml = aml_obj.browse(cr, uid, moves[0], context)
                    result[rpp.id] = (aml.id,aml.name)
        return result

    def _get_invoice_qty(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for rpp in self.browse(cr, uid, ids, context):
            res[rpp.id] = 0.0
            if rpp.invoice_line_id and rpp.invoice_line_id.id:
                res[rpp.id] = rpp.invoice_line_id.quantity
        return res
    
    def _get_aml_cost_qty(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for rpp in self.browse(cr, uid, ids, context):
            res[rpp.id] = 0.0
            if rpp.aml_cost_id and rpp.aml_cost_id.id:
                res[rpp.id] = rpp.aml_cost_id.quantity
        return res

    def _get_aml_inv_qty(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for rpp in self.browse(cr, uid, ids, context):
            res[rpp.id] = 0.0
            if rpp.aml_inv_id and rpp.aml_inv_id.id:
                res[rpp.id] = rpp.aml_inv_id.quantity
        return res      


    def _get_invoice_price(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for rpp in self.browse(cr, uid, ids, context):
            res[rpp.id] = 0.0
            if rpp.invoice_line_id and rpp.invoice_line_id.id:
                res[rpp.id] = rpp.invoice_line_id.price_unit
        return res

    def _get_aml_cost_price(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for rpp in self.browse(cr, uid, ids, context):
            res[rpp.id] = 0.0
            if rpp.aml_cost_id and rpp.aml_cost_id.id:
                if rpp.aml_cost_id.quantity and rpp.aml_cost_id.quantity>0:
                    price_unit = 0.0
                    if rpp.aml_cost_id.debit:
                        amount = rpp.aml_cost_id.debit
                    else:
                        amount = rpp.aml_cost_id.credit
                    price_unit = amount/rpp.aml_cost_id.quantity
                    res[rpp.id] = price_unit
        return res


    def _get_aml_inv_price(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for rpp in self.browse(cr, uid, ids, context):
            res[rpp.id] = 0.0
            if rpp.aml_inv_id and rpp.aml_inv_id.id:
                if rpp.aml_inv_id.quantity and rpp.aml_inv_id.quantity>0:
                    price_unit = 0.0
                    if rpp.aml_inv_id.debit:
                        amount = rpp.aml_inv_id.debit
                    else:
                        amount = rpp.aml_inv_id.credit
                    price_unit = amount/rpp.aml_inv_id.quantity
                    res[rpp.id] = price_unit
        return res


    def _get_prod_stock_before(self, cr, uid, ids, name, arg, context={}):
        res = {}
        prod_obj = self.pool.get('product.product')

        loc_ids = 11
        for line in self.browse(cr, uid, ids, context=context):
            #print 'fechaxxx: ',line.name
            startf = datetime.datetime.fromtimestamp(time.mktime(time.strptime(line.name,"%Y-%m-%d:%H:%M:%S")))
            #print 'ffff: ',startf
            start = DateTime(int(startf.year),1,1)
            #end = DateTime(int(startf.year),int(startf.month),int(startf.day))
            end = startf - datetime.timedelta(seconds=1)
            d1 = start.strftime('%Y-%m-%d %H:%M:%S')
            d2 = end.strftime('%Y-%m-%d %H:%M:%S')
            #print 'd1xxxxxxx: ',d1
            #print 'd2yyyyyyy: ',d2
            c = context.copy()
            c.update({'location': loc_ids,'from_date':d1,'to_date':d2})
            res.setdefault(line.id, 0.0)
            if line.product_id and line.product_id.id:
                prd = prod_obj.browse(cr, uid, line.product_id.id,context=c)
                res[line.id] = prd.qty_available
        return res

    def _get_prod_stock_after(self, cr, uid, ids, name, arg, context={}):
        res = {}
        prod_obj = self.pool.get('product.product')

        loc_ids = 11
        for line in self.browse(cr, uid, ids, context=context):
            startf = datetime.datetime.fromtimestamp(time.mktime(time.strptime(line.name,"%Y-%m-%d:%H:%M:%S")))
            start = DateTime(int(startf.year),1,1)
            end = startf + datetime.timedelta(seconds=1)
            d1 = start.strftime('%Y-%m-%d %H:%M:%S')
            d2 = end.strftime('%Y-%m-%d %H:%M:%S')
            c = context.copy()
            c.update({'location': loc_ids,'from_date':d1,'to_date':d2})
            res.setdefault(line.id, 0.0)
            if line.product_id and line.product_id.id:
                prd = prod_obj.browse(cr, uid, line.product_id.id,context=c)
                res[line.id] = prd.qty_available
        return res    

    def _get_invoice(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for rpp in self.browse(cr, uid, ids, context):
            res[rpp.id] = False
            if rpp.invoice_line_id and rpp.invoice_line_id.id:
                res[rpp.id] = rpp.invoice_line_id.invoice_id.id
        return res    

    def _get_date_invoice(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for rpp in self.browse(cr, uid, ids, context):
            res[rpp.id] = False
            if rpp.invoice_line_id and rpp.invoice_line_id.id:
                if rpp.invoice_line_id.invoice_id.date_invoice:
                    date = rpp.invoice_line_id.invoice_id.date_invoice
                    startf = datetime.datetime.fromtimestamp(time.mktime(time.strptime(date,"%Y-%m-%d")))
                    res[rpp.id] = startf.strftime('%Y-%m-%d:16:00:%S')
        return res

    def _get_stock_invoice(self, cr, uid, ids, name, arg, context={}):
        res = {}
        prod_obj = self.pool.get('product.product')

        loc_ids = 11
        for line in self.browse(cr, uid, ids, context=context):
            res.setdefault(line.id, 0.0)
            if line.date_inv:
                startf = datetime.datetime.fromtimestamp(time.mktime(time.strptime(line.date_inv,"%Y-%m-%d:%H:%M:%S")))             
                start = DateTime(int(startf.year),1,1)
                end = startf - datetime.timedelta(seconds=1)
                d1 = start.strftime('%Y-%m-%d %H:%M:%S')
                d2 = end.strftime('%Y-%m-%d %H:%M:%S')
                c = context.copy()
                c.update({'location': loc_ids,'from_date':d1,'to_date':d2})
                if line.product_id and line.product_id.id:
                    prd = prod_obj.browse(cr, uid, line.product_id.id,context=c)
                    res[line.id] = prd.qty_available
        return res


    def _compute_subtotal(self, cr, uid, ids, name, arg, context={}):
        res = {}

        loc_ids = 11
        avg=1430.96
        q=5.0
        #total=7154,8
        total=avg*q
        for line in self.browse(cr, uid, ids, context=context):
            subtot = 0.0
            res.setdefault(line.id, 0.0)
            
            if line.invoice_id and line.invoice_id.id:
                if line.location_dest_id.id == loc_ids and line.invoice_id.type == 'in_invoice':
                    subtot = line.picking_qty*line.invoice_price_unit

                if line.location_id.id == loc_ids and line.invoice_id.type == 'out_invoice':
                    subtot = line.picking_qty*avg

                if line.location_dest_id.id == loc_ids and line.invoice_id.type == 'in_refund':
                    if line.invoice_id.parent_id and line.invoice_id.parent_id.id:
                        for il in line.invoice_id.parent_id.invoice_line:
                            if il.product_id.id == line.product_id.id:
                                subtot = line.picking_qty*il.price_unit

#                if line.location_id.id == loc_ids and line.invoice_id.type == 'out_refund':
#                    subtot = line.picking_qty*avg

            res[line.id] = subtot
        return res    

    def _compute_total(self, cr, uid, ids, name, arg, context={}):
        res = {}

        loc_ids = 11
        avg=1430.96
        q=5.0
        #total=7154,8
#        total=avg*q
        tot = {}
        for line in self.browse(cr, uid, ids, context=context):
            tot.setdefault(line.product_id.id, 'xxx')
            res.setdefault(line.id, 0.0)
            
            if tot[line.product_id.id] == 'xxx':
                tot[line.product_id.id] = avg*q
            
            if line.invoice_id and line.invoice_id.id:
                if line.location_dest_id.id == loc_ids and line.invoice_id.type == 'in_invoice':
                    tot[line.product_id.id]+= line.subtotal

                if line.location_id.id == loc_ids and line.invoice_id.type == 'out_invoice':
                    tot[line.product_id.id]-= line.subtotal

                if line.location_dest_id.id == loc_ids and line.invoice_id.type == 'in_refund':
                    tot[line.product_id.id]-= line.subtotal
#                    if line.invoice_id.parent_id and line.invoice_id.parent_id.id:
#                        for il in line.invoice_id.parent_id.invoice_line:
#                            if il.product_id.id == line.product_id.id:
#                                subtot = line.picking_qty*il.price_unit

#                if line.location_id.id == loc_ids and line.invoice_id.type == 'out_refund':
#                    subtot = line.picking_qty*avg

#            print 'total: ',tot
            res[line.id] = tot[line.product_id.id]
        return res


    def _get_aml_inv(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        aml_obj = self.pool.get('account.move.line')
        for rpp in self.browse(cr, uid, ids, context):
            result[rpp.id] = ()
            if rpp.invoice_line_id and rpp.invoice_line_id.id:
                moves = self.aml_inv_get(cr, uid, [rpp.invoice_line_id.id])
                if moves:
                    aml = aml_obj.browse(cr, uid, moves[0], context)
                    result[rpp.id] = (aml.id,aml.name)
        return result
    

    def aml_cost_get(self, cr, uid, il_id):    
        res = []
        il_obj = self.pool.get('account.invoice.line')
        res = il_obj.move_line_id_cost_get(cr, uid, il_id)    
        return res

    
    def aml_inv_get(self, cr, uid, il_id):
        res = []
        il_obj = self.pool.get('account.invoice.line')
        res = il_obj.move_line_id_inv_get(cr, uid, il_id)
        return res
    
        
    _name = "report.profit.picking"
    _description = "Move by Picking"
    _auto = False
    _columns = {
        'name': fields.char('Date', size=20, readonly=True, select=True),
        'picking_id':fields.many2one('stock.picking', 'Picking', readonly=True, select=True),
        'purchase_line_id': fields.many2one('purchase.order.line', 'Purchase Line', readonly=True, select=True),
        'sale_line_id': fields.many2one('sale.order.line', 'Sale Line', readonly=True, select=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True, select=True),
        'location_id':fields.many2one('stock.location', 'Source Location', readonly=True, select=True),
        'location_dest_id':fields.many2one('stock.location', 'Dest. Location', readonly=True, select=True),                
        'stk_mov_id':fields.many2one('stock.move', 'Picking line', readonly=True, select=True),
        'picking_qty': fields.float('Picking quantity', readonly=True),        
        'type': fields.selection([
            ('out', 'Sending Goods'),
            ('in', 'Getting Goods'),
            ('internal', 'Internal'),
            ('delivery', 'Delivery')
            ],'Type', readonly=True, select=True),        
        'state': fields.selection([
            ('draft', 'Draft'),
            ('waiting', 'Waiting'),
            ('confirmed', 'Confirmed'),
            ('assigned', 'Available'),
            ('done', 'Done'),
            ('cancel', 'Cancelled')
            ],'Status', readonly=True, select=True),
        'aml_cost_id': fields.function(_get_aml_cost, method=True, type='many2one', relation='account.move.line', string='Cost entry'),
        'invoice_line_id': fields.function(_get_invoice_line, method=True, type='many2one', relation='account.invoice.line', string='Invoice line'),
        'invoice_qty': fields.function(_get_invoice_qty, method=True, type='float', string='Invoice quantity', digits=(16, int(config['price_accuracy']))),
        'aml_cost_qty': fields.function(_get_aml_cost_qty, method=True, type='float', string='Cost entry quantity', digits=(16, int(config['price_accuracy']))),
        'invoice_price_unit': fields.function(_get_invoice_price, method=True, type='float', string='Invoice price unit', digits=(16, int(config['price_accuracy']))),
        'aml_cost_price_unit': fields.function(_get_aml_cost_price, method=True, type='float', string='Cost entry price unit', digits=(16, int(config['price_accuracy']))), 
        'invoice_id': fields.function(_get_invoice, method=True, type='many2one', relation='account.invoice', string='Invoice'),
        'stock_before': fields.function(_get_prod_stock_before, method=True, type='float', string='Stock before', digits=(16, int(config['price_accuracy']))),
        'stock_after': fields.function(_get_prod_stock_after, method=True, type='float', string='Stock after', digits=(16, int(config['price_accuracy']))),
        'date_inv': fields.function(_get_date_invoice, method=True, type='char', string='Date invoice', size=20),
        'stock_invoice': fields.function(_get_stock_invoice, method=True, type='float', string='Stock invoice', digits=(16, int(config['price_accuracy']))),
        'subtotal': fields.function(_compute_subtotal, method=True, type='float', string='Subtotal', digits=(16, int(config['price_accuracy']))),
        'total': fields.function(_compute_total, method=True, type='float', string='Total', digits=(16, int(config['price_accuracy']))),
        'aml_inv_id': fields.function(_get_aml_inv, method=True, type='many2one', relation='account.move.line', string='Inv entry'),
        'aml_inv_price_unit': fields.function(_get_aml_inv_price, method=True, type='float', string='Inv entry price unit', digits=(16, int(config['price_accuracy']))),        
        'aml_inv_qty': fields.function(_get_aml_inv_qty, method=True, type='float', string='Inv entry quantity', digits=(16, int(config['price_accuracy']))),        
    }

    def init(self, cr):
        drop_view_if_exists(cr, 'report_profit_picking')
        cr.execute("""
            create or replace view report_profit_picking as (
            select
                sm.id as id,                
                to_char(sm.date_planned, 'YYYY-MM-DD:HH24:MI:SS') as name,
                sm.picking_id as picking_id,
                sp.type as type,                
                sm.purchase_line_id as purchase_line_id,
                sm.sale_line_id as sale_line_id,
                sm.product_id as product_id,
                sm.location_id as location_id,
                sm.location_dest_id as location_dest_id,                
                sm.id as stk_mov_id,
                sm.product_qty as picking_qty,
                sm.state as state
            from stock_picking sp
                right join stock_move sm on (sp.id=sm.picking_id)
                left join product_template pt on (pt.id=sm.product_id)
            where sm.state='done' and pt.type!='service'
            order by name
            )
        """)
report_profit_picking()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

