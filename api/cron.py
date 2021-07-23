# Create your tasks here
from datetime import datetime
from .models import RecievedOC, ProductoBodega, Log, Pedido, EmbassyOC, EmbassyXML
from .warehouse import despachar_producto, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto, fabricar_vacuna
import time
import math
from .business_logic import factibildad
from .OC import parse_js_date, crear_oc, obtener_oc, recepcionar_oc, rechazar_oc
import os
from .arrays_clients_ids_oc import IDS_DEV, IDS_PROD
from .arrays_almacenes_recep import RECEPCIONES_DEV, RECEPCIONES_PROD
from .INFO_SKU.info_sku import PRODUCTOS, FORMULA, NUESTRO_SKU

import os
from pathlib import Path
import environ

# Initialise environment variables

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(env_file=os.path.join(BASE_DIR, 'proyecto13/.env'))

if os.environ.get('DJANGO_DEVELOPMENT')=='true':
    ids_grupos = IDS_DEV
    ids_recepcion = RECEPCIONES_DEV
    user_ftp  = env('USER_FTP_DEV')
    pass_ftp  = env('PASS_FTP_DEV')
else:
    ids_grupos = IDS_PROD
    ids_recepcion = RECEPCIONES_PROD
    user_ftp  = env('USER_FTP_PROD')
    pass_ftp  = env('PASS_FTP_PROD')

def mover_recepcion_a_alm_central():
    almacen_recepcion= None
    almacen_central = None
    almancen_pulmon = None
    almancen_despacho = None
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['recepcion']:
            almacen_recepcion = almacen
        elif almacen['pulmon']:
            almacen_pulmon = almacen
        elif almacen['despacho']:
            almacen_despacho = almacen
        else:
            almacen_central = almacen

    params = {'almacenId': almacen_recepcion['_id']}
    stock_alm_recepción = obtener_stock(params).json()
    IDs_por_sku_alm_recepcion = {}
    try:
        if len(stock_alm_recepción) > 0:
            if int(almacen_central['totalSpace']) > int(almacen_central['usedSpace']):
                print('Moviendo productos al almacen central...')
                mensaje=''
                for sku in stock_alm_recepción:
                    IDs_por_sku_alm_recepcion[sku['_id']]= []
                    productos_almacen_recepcion = obtener_productos_almacen(
                        {"almacenId": almacen_recepcion['_id'], "sku": sku["_id"]}).json()
                    for producto_almacen in productos_almacen_recepcion:
                        IDs_por_sku_alm_recepcion[sku['_id']].append(producto_almacen['_id'])
                        ############### Instancia productoBodega
                        ###Chequear antes si ya existe por caso que no pueda moverlo al primer intento y ya se haya creado
                        try:
                            if ProductoBodega.objects.filter(id=producto_almacen['_id']).exists():
                                pass   ## listos
                            else:  ### Bajar cantidad en pedido, borrar si llega a 0, crear productoBodega
                                pedido = Pedido.objects.filter(sku=str(sku["_id"])).order_by('fecha_disponible').first()
                                id_pedido = pedido.id
                                if pedido.cantidad == 1:
                                    pedido.delete()
                                    # log_pedido = Log(mensaje=f"Recepción a Central: Se borró el pedido {id_pedido}")
                                    # log_pedido.save()
                                else:
                                    pedido.cantidad -= 1
                                producto_bodega = ProductoBodega(id = producto_almacen['_id'], sku=str(producto_almacen["sku"]), almacen=almacen_recepcion['_id'],\
                                    fecha_vencimiento=parse_js_date(producto_almacen["vencimiento"]))
                                log_producto = Log(mensaje=f"Recepción a Central: Llegó un producto del pedido {id_pedido} y se creó en bodega con id {producto_almacen['_id']}")
                                log_producto.save()
                                producto_bodega.save()
                                pedido.save()
                        except:
                            pass
                        #################
                for SKU in IDs_por_sku_alm_recepcion:
                    print(f'Moviendo productos de SKU {SKU}')
                    contador=0
                    for ID_producto in IDs_por_sku_alm_recepcion[SKU]:
                        time.sleep(1)
                        mover_entre_almacenes(
                                {'productoId': ID_producto, "almacenId": almacen_central['_id']})
                        contador+=1
                    mensaje+= f'Recepción a Central: Se han movido {contador} productos del SKU {SKU} al almacén central\n'
                print(mensaje)
                # log_1 = Log(mensaje=mensaje)
                # log_1.save()
            else:
                print('El almacen central está lleno')
                log_2 = Log(mensaje='Recepción a Central: El almacen central está lleno')
                log_2.save()
        else:
            print('No hay productos para mover desde el almacén de recepción')
    except Exception as err:
            log_3 = Log(mensaje='Recepción a Central: '+str(err))
            log_3.save()

def mover_pulmon_a_alm_recepcion():
    almacen_recepcion= None
    almacen_central = None
    almancen_pulmon = None
    almancen_despacho = None
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['recepcion']:
            almacen_recepcion = almacen
        elif almacen['pulmon']:
            almancen_pulmon = almacen
        elif almacen['despacho']:
            almacen_despacho = almacen
        else:
            almacen_central = almacen

    params = {'almacenId': almancen_pulmon['_id']}
    stock_alm_pulmon = obtener_stock(params).json()
    IDs_por_sku_alm_pulmon = {}
    try:
        if len(stock_alm_pulmon) > 0:
            if int(almacen_recepcion['totalSpace']) > int(almacen_recepcion['usedSpace']):
                print('Moviendo productos al almacen de despacho...')
                mensaje=''
                for sku in stock_alm_pulmon:
                    IDs_por_sku_alm_pulmon[sku['_id']]= []
                    productos_almacen_pulmon = obtener_productos_almacen(
                        {"almacenId": almancen_pulmon['_id'], "sku": sku["_id"]}).json()
                    for producto_almacen in productos_almacen_pulmon:
                        IDs_por_sku_alm_pulmon[sku['_id']].append(producto_almacen['_id'])
                        ############### Instancia productoBodega
                        ###Chequear antes si ya existe por caso que no pueda moverlo al primer intento y se haya creado
                        try:
                            if ProductoBodega.objects.filter(id=producto_almacen['_id']).exists():
                                pass   ## listos
                            else:  ### Bajar cantidad en pedido, borrar si llega a 0, crear productoBodega
                                pedido = Pedido.objects.filter(sku=str(sku["_id"])).order_by('fecha_disponible').first()
                                id_pedido = pedido.id
                                if pedido.cantidad == 1:
                                    pedido.delete()
                                    # log_pedido = Log(mensaje=f"Pulmón a Recepción: Se borró el pedido {id_pedido}")
                                    # log_pedido.save()
                                else:
                                    pedido.cantidad -= 1
                                producto_bodega = ProductoBodega(id = producto_almacen['_id'], sku=str(producto_almacen["sku"]), almacen=almancen_pulmon['_id'],\
                                    fecha_vencimiento=parse_js_date(producto_almacen["vencimiento"]))
                                producto_bodega.save()
                                pedido.save()
                                log_producto = Log(mensaje=f"Pulmón a Recepción: Llegó un producto del pedido {id_pedido} y se creó en bodega con id {producto_almacen['_id']}")
                                log_producto.save()
                        except:
                            pass
                        #################
                        
                for SKU in IDs_por_sku_alm_pulmon:
                    print(f'Moviendo productos de SKU {SKU}')
                    contador=0
                    for ID_producto in IDs_por_sku_alm_pulmon[SKU]:
                        time.sleep(1)
                        mover_entre_almacenes(
                                {'productoId': ID_producto, "almacenId": almacen_recepcion['_id']})
                        contador+=1
                    mensaje+= f'Pulmón a Recepción: Se han movido {contador} productos del SKU {SKU} al almacén de recepción\n'
                print(mensaje)
                # log_1 = Log(mensaje=mensaje)
                # log_1.save()
            else:
                print('El almacen de recepción está lleno')
                log_2 = Log(mensaje='Pulmón a Recepción: El almacen de recepción está lleno')
                log_2.save()
        else:
            print('No hay productos para mover desde el almacén de recepción')
    except Exception as err:
        log_3 = Log(mensaje='Pulmón a Recepción: '+(err))
        log_3.save()

def revision_oc():
    not_completed_embassy_oc = EmbassyOC.objects.filter(estado="aceptada")
    for orden in not_completed_embassy_oc:
        log = Log(mensaje = f"Actualizando Embassy OC de id {orden.id}")
        log.save()
        if orden.cantidad_despachada < orden.cantidad:
            falta = orden.cantidad - orden.cantidad_despachada
            lista_vacunas = ProductoBodega.objects.filter(oc_reservada='', sku = str(orden.sku))
            vacunas_disponible = ProductoBodega.objects.filter(oc_reservada='', sku = str(orden.sku)).count()
            if vacunas_disponible <= falta  :
                for vacuna in lista_vacunas:
                    vacuna.oc_reservada = orden.id
                    vacuna.save()
            else:
                contador = 0
                for vacuna in lista_vacunas:
                    vacuna.oc_reservada = orden.id
                    vacuna.save()
                    contador += 1
                    if contador == falta:
                        break
                orden.estado = "finalizada"
                orden.save()
            orden.cantidad_despachada = ProductoBodega.objects.filter(oc_reservada=orden.id, sku = str(orden.sku)).count()
        else:
            orden.estado = "finalizada"
            orden.save()
        if orden.estado == "aceptada":
            ingredientes = FORMULA[str(orden.sku)]
            cantidad_faltante = int(orden.cantidad) - int(orden.cantidad_despachada)
            lote = int(PRODUCTOS[str(orden.sku)]['Lote producción'])
            lotes_por_pedir = math.ceil(cantidad_faltante/lote)
            for ingrediente in ingredientes.keys():
                guardado = ProductoBodega.objects.filter(oc_reservada=orden.id, sku=ingrediente).count()
                if guardado < (int(ingredientes[ingrediente]) * lotes_por_pedir):
                    productos_disponibles = ProductoBodega.objects.filter(sku=ingrediente, oc_reservada='')
                    cantidad_disponible = productos_disponibles.count()
                    cantidad = (int(ingredientes[ingrediente]) * lotes_por_pedir) - int(guardado)
                    if cantidad_disponible <= cantidad:
                        for producto in productos_disponibles:
                            producto.oc_reservada = orden.id
                            producto.save()
                            print(f"Asignando producto de id {producto.id} a OC de id {orden.id}")
                            log = Log(mensaje=f"Revision Embassy OC: Asignando producto de id {producto.id} a OC de id {orden.id}")
                            log.save()
                    else:
                        contador = 0
                        for producto in productos_disponibles:
                            producto.oc_reservada = orden.id
                            producto.save()
                            log = Log(mensaje=f"Revision Embassy OC: Asignando producto de id {producto.id} a OC de id {orden.id}")
                            log.save()
                            print(f"Asignando producto de id {producto.id} a OC de id {orden.id}")
                            contador += 1
                            if contador == cantidad:
                                break
            ready = True
            for ingrediente in ingredientes.keys():
                disponible = ProductoBodega.objects.filter(sku=ingrediente, oc_reservada=orden.id).count()
                if int(disponible) < (int(ingredientes[ingrediente]) * lotes_por_pedir):
                    ready = False
            if ready:
                lote = int(PRODUCTOS[str(orden.sku)]['Lote producción'])
                por_pedir = math.ceil(orden.cantidad/lote) * lote
                fabricar_vacuna({'sku': str(orden.sku), 'cantidad': por_pedir})

    not_completed_oc = RecievedOC.objects.filter(estado="aceptada")
    for orden in not_completed_oc:
        print(f"Actualizando OC de id {orden.id}")
        orden.cantidad_despachada = ProductoBodega.objects.filter(oc_reservada=orden.id).count()
        orden.save()
        sku = orden.sku
        cantidad = orden.cantidad - orden.cantidad_despachada
        if cantidad > 0:
            productos_disponibles = ProductoBodega.objects.filter(sku=str(sku), oc_reservada='')
            cantidad_disponible = productos_disponibles.count()
            if cantidad_disponible <= cantidad:
                for producto in productos_disponibles:
                    producto.oc_reservada = orden.id
                    producto.save()
                    print(f"Asignando producto de id {producto.id} a OC de id {orden.id}")
                    log = Log(mensaje=f"Revision OC: Asignando producto de id {producto.id} a OC de id {orden.id}")
                    log.save()
                orden.cantidad_despachada = ProductoBodega.objects.filter(oc_reservada=orden.id).count()
            else:
                contador = 0
                for producto in productos_disponibles:
                    producto.oc_reservada = orden.id
                    producto.save()
                    log = Log(mensaje=f"Revision OC: Asignando producto de id {producto.id} a OC de id {orden.id}")
                    log.save()
                    print(f"Asignando producto de id {producto.id} a OC de id {orden.id}")
                    contador += 1
                    if contador == cantidad:
                        break
                orden.cantidad_despachada = ProductoBodega.objects.filter(oc_reservada=orden.id).count()
        if orden.cantidad_despachada >= orden.cantidad:
            orden.estado = "finalizada"
        orden.save()
        print(f"OC de id {orden.id} actualizada")

def mover_despacho():
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['recepcion']:
            almacen_recepcion = almacen
        elif almacen['pulmon']:
            almacen_pulmon = almacen
        elif almacen['despacho']:
            almacen_despacho = almacen
        else:
            almacen_central = almacen
    ids_almacen = [almacen_recepcion['_id'], almacen_central['_id'], almacen_pulmon['_id']]
    productos_despacho = ProductoBodega.objects.filter(almacen__in=ids_almacen).exclude(oc_reservada='')
    for producto in productos_despacho:
        if producto.almacen != almacen_pulmon['_id']:
            try:
                mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_despacho['_id']})
                print(f'Se han movido 1 producto del SKU {producto.sku} al almacén desapcho\n')
                # log = Log(mensaje=f'Mover despacho: Se han movido 1 producto del SKU {producto.sku} al almacén despacho\n')
                # log.save()
                time.sleep(1)
            except:
                print(f'Alamacen Despacho se encuentra lleno')
                break
        else:
            try:
                mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_recepcion['_id']})
                print(f'Se han movido 1 producto del SKU {producto.sku} al almacén recepción\n')
                # log = Log(mensaje=f'Mover despacho: Se han movido 1 producto del SKU {producto.sku} al almacén recepción\n')
                # log.save()
                time.sleep(1)
                try:
                    mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_despacho['_id']})
                    # log = Log(mensaje=f'Mover despacho: Se han movido 1 producto del SKU {producto.sku} al almacén despacho\n')
                    # log.save()
                    time.sleep(1)
                except:
                    print(f'Alamacen Despacho se encuentra lleno')
                    break
            except:
                print(f'Alamcen Recepción se encuentra lleno')
                break

def despachar_vacunas():
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['despacho']:
            almacen_despacho = almacen
    skus_vacunas = list(FORMULA.keys())
    vacunas_para_despachar = ProductoBodega.objects.filter(almacen=almacen_despacho['_id'], sku__in=skus_vacunas).exclude(oc_reservada='')
    for vacuna in vacunas_para_despachar:
        params = {
            "productoId": vacuna.id,
            "oc": vacuna.oc_reservada,
            "direccion": "embajada",
            "precio": 1
        }
        try:
            despachar_producto(params)
            vacuna.delete()
        except:
            log = Log(mensaje=f'No se pudo despachar vacuna de id {vacuna.id} asociada a la OC {vacuna.oc_reservada}')
            log.save()

def despachar():
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['despacho']:
            almacen_despacho = almacen
    try:
        productos_para_despachar = ProductoBodega.objects.filter(almacen=almacen_despacho['_id']).exclude(oc_reservada='')
        print(productos_para_despachar)
        for producto in productos_para_despachar:
            print('despachando...')
            oc = producto.oc_reservada
            try:
                oc_object = RecievedOC.objects.filter(id=oc)
                posicion = ids_grupos.index(oc_object[0].cliente)
                almacen_id = ids_recepcion[posicion]
                respuesta = mover_entre_bodegas({'productoId': producto.id, 'almacenId': almacen_id, 'oc': oc, 'precio': oc_object[0].precio_unitario}).json()
                try:
                    print(f"Despachar: El producto de id {producto.id} fue despachado al almacen {almacen_id}")
                    # log = Log(mensaje=f"El producto de id {producto.id} fue despachado al almacen {almacen_id}")
                    # log.save()
                    producto.delete()
                except:
                    print(respuesta["error"])
                    log = Log(mensaje=respuesta["error"])
                    log.save()
                time.sleep(1)
            except:
                pass
    except Exception as err:
        log = Log(mensaje='Despachar: '+str(err))
        log.save()

def revison_stock_propio():
    for sku in NUESTRO_SKU[:-6]:
        if ProductoBodega.objects.filter(sku=sku, oc_reservada = '').exists():
            cantidad_productos_disponibles = ProductoBodega.objects.filter(sku=sku, oc_reservada = '').count()
            if cantidad_productos_disponibles < 24:
                lote = int(PRODUCTOS[sku]['Lote producción'])
                por_pedir = math.ceil((24 - cantidad_productos_disponibles)/lote) * lote
                fabricar_producto({'sku': sku, 'cantidad': por_pedir})
        else:
            lote = int(PRODUCTOS[sku]['Lote producción'])
            por_pedir = math.ceil((24/lote) * lote)
            fabricar_producto({'sku': sku, 'cantidad': por_pedir})

def revision_stock_para_vacunas():
    for vacuna in FORMULA.keys():
        if ProductoBodega.objects.filter(sku=vacuna, oc_reservada = '').exists():
            cantidad_vacunas_disponibles = ProductoBodega.objects.filter(sku=vacuna, oc_reservada = '').count()
            if cantidad_vacunas_disponibles < int(PRODUCTOS[vacuna]['Lote producción']):
                lote = int(PRODUCTOS[vacuna]['Lote producción'])
                por_pedir = math.ceil((int(PRODUCTOS[vacuna]['Lote producción']) - cantidad_vacunas_disponibles)/lote) * lote
                fabricar_vacuna({"sku": str(vacuna), "cantidad": por_pedir})
        else:
            lote = int(PRODUCTOS[vacuna]['Lote producción'])
            fabricar_vacuna({"tipo": str(vacuna), "cantidad": lote})

def eliminar():
    for producto in ProductoBodega.objects.filter(fecha_vencimiento__lte=datetime.now()):
        producto.delete()
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['recepcion']:
            almacen_recepcion = almacen
        elif almacen['pulmon']:
            almacen_pulmon = almacen
        elif almacen['despacho']:
            almacen_despacho = almacen
        else:
            almacen_central = almacen
    productos_despacho = ProductoBodega.objects.filter(almacen__in=almacen_despacho['_id']).exclude(oc_reservada='')
    embajadas = EmbassyOC.objects.all()
    embajada = [i.id for i in embajadas]
    for producto in productos_despacho:
        if producto.oc_reservada in embajada:
            producto.oc_reservada = ''
            producto.save()

import pysftp
import paramiko
import fnmatch
import xml.etree.ElementTree as ET

class My_Connection(pysftp.Connection):
    def __init__(self, *args, **kwargs):
        try:
            if kwargs.get('cnopts') is None:
                kwargs['cnopts'] = pysftp.CnOpts()
        except pysftp.HostKeysException as e:
            self._init_error = True
            raise paramiko.ssh_exception.SSHException(str(e))
        else:
            self._init_error = False

        self._sftp_live = False
        self._transport = None
        super().__init__(*args, **kwargs)

    def __del__(self):
        if not self._init_error:
            self.close()




def obtener_oc_embajadas():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    try:
        with My_Connection('beirut.ing.puc.cl', username=user_ftp, password=pass_ftp, cnopts=cnopts) as sftp:
            for filename in sftp.listdir('/pedidos/'):
                if fnmatch.fnmatch(filename, "*.xml"):
                    try:
                        EXML = EmbassyXML(name=filename)
                        EXML.save()
                        sftp.get("/pedidos/" + filename, os.path.join(BASE_DIR, 'api/embajadas/'+ filename) )
                        root = ET.parse(os.path.join(BASE_DIR, 'api/embajadas/'+ filename))
                        tree_root = root.getroot()
                        for elem in tree_root:
                            if str(elem.tag)=='id':
                                id = str(elem.text)
                                orden_de_compra = obtener_oc(id).json()[0]
                                embassyOc = EmbassyOC(id=id,
                                cliente=orden_de_compra["cliente"],
                                proveedor=orden_de_compra["proveedor"],
                                sku=orden_de_compra["sku"],
                                fecha_entrega=parse_js_date(
                                    orden_de_compra["fechaEntrega"]),
                                cantidad=orden_de_compra["cantidad"],
                                cantidad_despachada=orden_de_compra["cantidadDespachada"],
                                precio_unitario=orden_de_compra["precioUnitario"],
                                canal=orden_de_compra["canal"],
                                estado=orden_de_compra["estado"],
                                created_at=parse_js_date(
                                    orden_de_compra["created_at"]),
                                updated_at=parse_js_date(
                                    orden_de_compra["updated_at"])
                                )
                                embassyOc.save()
                                print('Creando OC de embajada...')
                                # TODO: Aceptar la OC de la embajada
                    except Exception as e:
                            print(str(e))
                            
                    


    except paramiko.ssh_exception.SSHException as e:
        log_error = Log(mensaje=f"Problemas de conexión a la casilla FTP")
        log_error.save()
        print('SSH error, you need to add the public key of your remote in your local known_hosts file first.', e)

def factibilidad_oc_embajada():
    try:
        ordenes_creadas = EmbassyOC.objects.filter(
                estado="creada"
            )
        for oc in ordenes_creadas:
            # log = Log(mensaje=f"Viendo factibilidad OC embajada {oc.id}")
            # log.save()
            log = Log(mensaje=f"Aceptando OC embajada {oc.id}")
            log.save()
            recepcionar_oc(oc.id, True)
            # factible =factibildad(oc.sku,oc.cantidad,oc.fecha_entrega,oc.id)
            # if factible:
            #     log = Log(mensaje=f"Aceptando OC embajada {oc.id}")
            #     log.save()
            #     recepcionar_oc(oc.id, True)
            # else:
            #     log = Log(mensaje=f"Rechazando OC embajada {oc.id}")
            #     log.save()
            #     rechazar_oc(oc.id, {"rechazo": "No podemos despachar"},True)

    except Exception as err:
        log_error = Log(mensaje=f"Problemas con la factibilidad OC embajada: {err}")
        log_error.save()
