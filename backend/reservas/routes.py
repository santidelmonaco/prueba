from flask import jsonify, request
from database.db import get_connection
from . import reservas_bp
import qrcode
import os

# Este endpoint mostrará todas las reservas vinculadas a un usuario.
# Se recibirá, a traves de la URI, un 'id' el cual servirá para identificar las reservas relacionadas al usuario
@reservas_bp.route("/usr/<int:id_usr>")
def get_reservas_usr(id_usr):
    conn=get_connection()                                              
    cursor=conn.cursor(dictionary=True)                                                

    qsql_reservas_usr="""SELECT 
                            r.id_reserva,
                            r.id_usr,
                            r.id_comercio,
                            r.nombre_bajo_reserva,
                            r.email,
                            r.telefono,
                            r.cant_personas, 
                            r.fecha_reserva, 
                            r.solicitud_especial,
                            r.estado_reserva,
                            c.nombre_comercio 
                            FROM reservas r 
                            JOIN comercios c ON c.id_comercio=r.id_comercio
                            WHERE id_usr=%s"""
    
    cursor.execute(qsql_reservas_usr,(id_usr,))
    reservas_usuario=cursor.fetchall()

    cursor.close()
    conn.close()
    if not reservas_usuario:
        return jsonify({"ERROR":f"No se encontró ningun registro relacionado al ID USUARIO:{id_usr}"}),404
    else:
        return jsonify(reservas_usuario),200

# Este endpoint mostrará todas las reservas vinculadas a un comercio
# Se recibirá, a traves de la URI, un 'id' el cual servirá para identificar las reservas relacionadas al comercio
@reservas_bp.route("/comercio/<int:id_comercio>")
def get_reservas_comercio(id_comercio):
    conn=get_connection()
    cursor=conn.cursor(dictionary=True)

    qsql_reservas_comercio="""SELECT * FROM reservas WHERE id_comercio=%s"""
    cursor.execute(qsql_reservas_comercio,(id_comercio,))
    reservas_comercio=cursor.fetchall()

    cursor.close()
    conn.close()
    if not reservas_comercio:
        return jsonify({"ERROR":f"No se encontró ningun registro relacionado al ID COMERCIO:{id_comercio}"}),404
    else:
        return jsonify(reservas_comercio),200
    
# Este endpoint mostrará toda la información relacionada a una reserva almacenada en la BDD
# Se recibirá, a traves de la URI, un 'id' el cual servirá para identificar la reserva en cuestión
@reservas_bp.route("/<int:id_reserva>")
def get_reserva(id_reserva):
    conn=get_connection()
    cursor=conn.cursor(dictionary=True)

    qsql_reserva_info="""SELECT * FROM reservas WHERE id_reserva=%s"""
    cursor.execute(qsql_reserva_info,(id_reserva,))

    reserva_encontrada=cursor.fetchone()

    cursor.close()
    conn.close()

    if not reserva_encontrada:
        return jsonify({"ERROR":f"No se encontró ningun registro vinculado al ID RESERVA:{id_reserva}"}), 404
    else:
        return jsonify(reserva_encontrada),200

# Este endpoint va a agregar una nueva reserva a la BDD. El mismo va a recibir un archivo JSON con toda la informacion requerida para realizar la operación
@reservas_bp.route("/agregar", methods=["POST"])
def agregar_reserva():
    body_request=request.get_json()

    claves_validas=["id_usr","id_comercio","nombre_bajo_reserva",
                      "email","telefono","cant_personas",
                      "fecha_reserva","solicitud_especial"]
    for clave in claves_validas:
        if clave not in body_request:
            return jsonify({"ERROR":f"Falta la clave '{clave}' en la petición"}),400

    conn=get_connection()
    cursor=conn.cursor()

    qsql_nueva_reserva=f""" INSERT INTO reservas 
                            (id_reserva,id_usr,id_comercio,nombre_bajo_reserva,email,telefono,cant_personas,fecha_reserva,solicitud_especial,estado_reserva) 
                            VALUES 
                            (default,%s,%s,%s,%s,%s,%s,%s,%s,default);"""
    
    cursor.execute(qsql_nueva_reserva,(body_request["id_usr"],body_request["id_comercio"],body_request["nombre_bajo_reserva"],
                                       body_request["email"],body_request["telefono"],body_request["cant_personas"],
                                       body_request["fecha_reserva"],body_request["solicitud_especial"]))

    conn.commit()                                           # Guardo los nuevos cambios realizados

    # Creo un código QR vinculado a la reserva en cuestión
    # Es necesario que en la URL este la IP local asi cualquier dispositivo de la misma red puede acceder al servidor Flask utilizando esa dirección. Permitiendo asi, a un telefono conectado a la misma red, escanear el QR para confirmar la reserva
    qr_reserva=qrcode.make(f"http://192.168.0.8:8100/reserva/estado/{cursor.lastrowid}")
    qr_reserva.save(f"../frontend/static/media/img/qr_reserva{cursor.lastrowid}.png")

    cursor.close()
    conn.close()
    return jsonify({"msg":"Reserva realizada con éxito"}),201

# Este endpoint eliminará de la BDD una reserva
# Se recibirá, a traves de la URI, un 'id' el cual permitirá identificar cual será el registro a eliminar
@reservas_bp.route("/eliminar/<int:id_reserva>", methods=["DELETE"])
def eliminar_reserva(id_reserva):
    conn=get_connection()
    cursor=conn.cursor()

    qsql_eliminar_reserva="""DELETE FROM reservas WHERE id_reserva=%s"""
    cursor.execute(qsql_eliminar_reserva,(id_reserva,))

    conn.commit()                           # Guardo los cambios realizados

    ruta_img_qr=f"../frontend/static/media/img/qr_reserva{id_reserva}.png"
    if os.path.exists(ruta_img_qr):
        os.remove(ruta_img_qr)

    cursor.close()
    conn.close()
    return jsonify({"msg":"Reserva eliminada con éxito"}),200

# Este endpoit editará la información de una reserva almacenada en la BDD
# Recibirá un archivo JSON el cual contedrá toda la información a editar
@reservas_bp.route("/editar", methods=["PUT"])
def editar_reserva():
    body_request=request.get_json()

    claves_validas=["id_reserva","id_usr","id_comercio","nombre_bajo_reserva","email",
                    "telefono","cant_personas","fecha_reserva","solicitud_especial","estado_reserva"]
    for clave in claves_validas:
        if clave not in body_request:
            return jsonify({"ERROR":f"Falta la clave {clave} en la petición"}),400
    
    conn=get_connection()
    cursor=conn.cursor()

    qsql_editar_reserva=f"""UPDATE reservas
                            SET 
                            {claves_validas[1]}=%s,
                            {claves_validas[2]}=%s,
                            {claves_validas[3]}=%s,
                            {claves_validas[4]}=%s,
                            {claves_validas[5]}=%s,
                            {claves_validas[6]}=%s,
                            {claves_validas[7]}=%s,
                            {claves_validas[8]}=%s,
                            {claves_validas[9]}=%s 
                            WHERE {claves_validas[0]}=%s;"""
    
    cursor.execute(qsql_editar_reserva,(body_request["id_usr"],body_request["id_comercio"],body_request["nombre_bajo_reserva"],
                                        body_request["email"], body_request["telefono"], body_request["cant_personas"], 
                                        body_request["fecha_reserva"], body_request["solicitud_especial"], body_request["estado_reserva"], 
                                        body_request["id_reserva"]))

    conn.commit()                           # Guardo los cambios realizados
    cursor.close()
    conn.close()
    return jsonify({"msg":"Reserva actualizada"}),200
    
# Este endpoint modificará el estado de una reserva para asi poder confirmarla. Se recibirá a traves de un parametro dinamico de la URI el ID de la misma
# Implementación a futuro.
#   Luego de pasado un determinado tiempo, el estado de la reserva será 'False'
#   Realizar algun tipo de animación con el front o algo por el estilo para mostrar que la reserva se confirmo
@reservas_bp.route("/estado/<int:id_reserva>")
def modificar_estado(id_reserva):
    conn=get_connection()
    cursor=conn.cursor(dictionary=True)

    # Actualizo el estado de la reserva
    qsql_nuevo_estado="""UPDATE reservas
                         SET
                            estado_reserva=True
                         WHERE id_reserva=%s;"""
    cursor.execute(qsql_nuevo_estado,(id_reserva,))

    conn.commit()                           # Guardo los cambios realizados
    cursor.close()
    conn.close()
    return jsonify({"msg":"Estado de reserva actualizado"}),200
