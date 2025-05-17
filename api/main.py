import os

import cv2
import face_recognition
import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from crud import crudEmpleado, crudAdmintrador
import uuid
from typing import Optional
from datetime import datetime, timedelta, date, time

from crud.crudAdmintrador import AdminCRUD
from crud.crudEmpleado import RegistroHorario
from crud.crudEmpleado import Empleado
from pydantic import BaseModel
from typing import List


# Dato biometrico, lo voy a usar para probar el endpoint regitrar horario
# Funcion que tengo en la versión 3 del reco (otro repo)
def extraer_vector(imagen_bytes: bytes):
    np_arr = np.frombuffer(imagen_bytes, np.uint8)
    imagen_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    vectores = face_recognition.face_encodings(imagen_np)
    if vectores:
        return vectores[0]
    return None

def obtenerDatoBiometrico():
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_imagen = os.path.join(ruta_base, "../personas/personaAutorizada1.jpg")
    with open(ruta_imagen, "rb") as imagen:
        contenido = imagen.read()
        vector_neutro = extraer_vector(contenido)
    return vector_neutro


class Empleado(BaseModel):
    nombre: str
    apellido: str
    tipo_identificacion: str
    numero_identificacion: str
    fecha_nacimiento: str
    correo_electronico: str
    telefono: str
    calle: str
    numero_calle: int
    localidad: str
    partido: str
    provincia: str
    genero: str
    pais_nacimiento: str
    estado_civil: str

class EmpleadoUpdate(BaseModel):
    telefono: Optional[str] = None
    correo_electronico: Optional[str] = None
    calle: Optional[str] = None
    numero_calle: Optional[str] = None
    localidad: Optional[str] = None
    partido: Optional[str] = None  # Nueva variable agregada
    provincia: Optional[str] = None

class AsistenciaManual(BaseModel):
    id_empleado: int
    tipo: str
    fecha: date
    hora: time
    estado_asistencia: Optional[str] = None

app = FastAPI()

@app.post("/empleados/")
def crear_empleado(empleado: Empleado):
    try:
        empleado = AdminCRUD.crear_empleado(empleado)
        return {
            "nombre": empleado.nombre,
            "apellido": empleado.apellido,
            "tipo_identificacion": empleado.tipo_identificacion,
            "numero_identificacion": empleado.numero_identificacion,
            "fecha_nacimiento": empleado.fecha_nacimiento,
            "correo_electronico": empleado.correo_electronico,
            "telefono": empleado.telefono,
            "calle": empleado.calle,
            "numero_calle": empleado.numero_calle,
            "localidad": empleado.localidad,
            "partido": empleado.partido,
            "provincia": empleado.provincia,
            "genero": empleado.genero,
            "pais_nacimiento": empleado.pais_nacimiento,
            "estado_civil": empleado.estado_civil
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/empleados/{numero_identificacion}")
def obtener_empleado(numero_identificacion: str):
    empleado = AdminCRUD.obtener_detalle_empleado(numero_identificacion)
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return empleado

# No puedo probarlo porque no hay registros laborales
@app.post("/registros/")
def registrar_horario(empleado_id: str, vectorBiometrico: str):
    try:
        registro = RegistroHorario.registrar_asistencia(empleado_id, obtenerDatoBiometrico()) #Voy a probar con un vector predeterminado
        return registro
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/registros/{empleado_id}")
def obtener_registros(
    empleado_id: str,
    año: Optional[int] = None,
    mes: Optional[int] = None
):
    if año and mes:
        registros = RegistroHorario.obtener_registros_mensuales(empleado_id, año, mes)
    else:
        registros = RegistroHorario.obtener_todos(empleado_id)
    return [r for r in registros]

# Creo que está bien, tengo que verificarlo con un registro de la base de datos
@app.get("/horas/{empleado_id}")
def calcular_horas(empleado_id: str, año: int, mes: int):
    horas = RegistroHorario.calcular_horas_mensuales(empleado_id, año, mes)
    return {"horas_trabajadas": horas}

# Actualizar datos de empleado
@app.put("/empleados/{empleado_id}/datos-personales")
def actualizar_datos_empleado(
    empleado_id: int,
    datos: EmpleadoUpdate,
    # Agrega autenticación para que solo el empleado o admin pueda actualizar
):
    try:
        empleado_actualizado = Empleado.actualizar_datos_personales(
            id_empleado=empleado_id,
            telefono=datos.telefono,
            correo_electronico=datos.correo_electronico,
            calle=datos.calle,
            numero_calle=datos.numero_calle,
            localidad=datos.localidad,
            partido=datos.partido,  # Nueva variable agregada
            provincia=datos.provincia
        )
        return empleado_actualizado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Registro manual de asistencia (admin)
@app.post("/admin/registros/manual", tags=["Admin"])
def registrar_asistencia_manual(
    registro: AsistenciaManual,
    # Agrega dependencia de autenticación de admin:
    # current_user: dict = Depends(verificar_admin)
):
    try:
        nuevo_registro = RegistroHorario.registrar_asistencia_manual(
            id_empleado=registro.id_empleado,
            tipo=registro.tipo,
            fecha=registro.fecha,
            hora=registro.hora,
            estado_asistencia=registro.estado_asistencia
        )
        return nuevo_registro
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

# Obtener todos los empleados (para listados)
@app.get("/empleados/")
def listar_empleados():
    try:
        empleados = AdminCRUD.obtener_empleados()
        return [e for e in empleados]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Búsqueda avanzada de empleados
@app.get("/empleados/buscar/", response_model=List[dict])
def buscar_empleados(
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    dni: Optional[str] = None
):
    empleados = Empleado.buscar_avanzado(
        nombre=nombre,
        apellido=apellido,
        dni=dni
    )
    return [e for e in empleados]