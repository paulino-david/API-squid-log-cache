
############################ Seccion de lectura del  archivo log de la cache #################################
ETag = None

def leer_cache():

	with open ("/var/log/squid/cache.log", "r", encoding="utf-8") as log_cache:

		cache = log_cache.read()

	return cache.split("\n")

#Lista de logs a enviar bien or estructurado con metodos de cadena

def ordenar(fila):

	if "|" in fila:

		cabecera,mensaje = fila.split("|",1)

		fecha = cabecera[:10]
		tiempo = cabecera[11:19]
		proceso = cabecera[20:].split()

		return {"fecha":fecha,"tiempo":tiempo,"proceso":proceso,"mensaje":mensaje}

	return {"fecha":fila[:10],"tiempo":fila[11:19],"proceso":"","mensaje":fila[20:]}


######################## Generar ETag ###########################

def generar_ETag():

	archivo = "\n".join(leer_cache()).encode()

	new_ETag = '"'+hashlib.md5(archivo).hexdigest()+'"'

	return new_ETag

######################### Seccion de hilo (threading) #################################
import json


## Libreria para crear ETags
import hashlib

######################## Crear un ETag #######################
def cliente(socket,addr):

	global ETag

	with socket:

		cache_HTTP = [ordenar(fila) for fila in leer_cache() if "|" in fila]

		mensaje_recv= socket.recv(1024).decode()
		cabecera_cliente = mensaje_recv.split("\r\n")

		mensaje_env = json.dumps({"respuesta":cache_HTTP})
		ETag_cliente = cabecera_cliente[-3].split(":",1)

		if "If-None-Match" in ETag_cliente:

			if ETag_cliente[1].strip()==ETag.strip():

				cabecera = f"""HTTP/1.1 304 Not-Modified\r\nContent-type: application/json\r\nCache-Control:public, no-cache\r\nContent-length: {len(mensaje_env)}\r\nAccess-Control-Expose-Headers: {ETag.strip()}\r\nAccess-Control-Allow-Origin:*\r\nConnection: close\r\n"""
				socket.sendall(cabecera.encode())

				return

		ETag = generar_ETag()

		cabecera = f"""HTTP/1.1 200 OK\r\nETag:{ETag}\r\nContent-type: application/json\r\nCache-Control:public, no-cache\r\nContent-length: {len(mensaje_env)}\r\nAccess-Control-Expose-Headers: {ETag.strip()}\r\nAccess-Control-Allow-Origin:*\r\nConnection: close\r\n\r\n"""

		socket.sendall(cabecera.encode()+mensaje_env.encode())

		print("Cliente:",addr)

		cabecera_cliente = mensaje_recv.split("\r\n")

		print("Mesnaje_recv:",cabecera_cliente)

		print("\nMensaje_env:",cabecera)

#		print("\nMensaje_env:",cabecera+mensaje_env,"\n\n")

########################## Seccion del servidor Socket #################################

import socket, threading


IP = socket.gethostbyname(socket.gethostname())

try:

	with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as servidor_socket:

		servidor_socket.bind((IP,5550))

		servidor_socket.listen()

		print("Servidor arrancado...\n")

		while True:

			socket_cliente, IP_cliente = servidor_socket.accept()

			hilo = threading.Thread(target = cliente, args = (socket_cliente,IP_cliente))
			hilo.start()


except KeyboardInterrupt:

	print("Servidor interrumpido por un Ctrl + C")
