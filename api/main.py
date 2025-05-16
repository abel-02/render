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
def crear_empleado(nombre: str,apellido: str, tipo_identificacion: str, numero_identificacion: str,
                        fecha_nacimiento: str,correo_electronico: str, telefono: str,
                        calle: str, numero_calle,localidad: str,partido: str,
                        provincia: str,genero,nacionalidad: str,estado_civil: str):
    try:
        empleado = Empleado.crear(nombre,apellido,tipo_identificacion, numero_identificacion,
                        fecha_nacimiento,correo_electronico, telefono,
                        calle, numero_calle,localidad,partido,
                        provincia,genero,nacionalidad,estado_civil)
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
            "nacionalidad": empleado.nacionalidad,
            "estado_civil": empleado.estado_civil
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/empleados/{dni}")
def obtener_empleado(dni: str):
    empleado = AdminCRUD.obtener_por_dni(dni)
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return empleado.__dict__

@app.post("/registros/")
def registrar_horario(empleado_id: str, tipo: str):
    try:
        registro = RegistroHorario.registrar(empleado_id, tipo)
        return registro.__dict__
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
    return [r.__dict__ for r in registros]

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
        return empleado_actualizado.__dict__
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
        return nuevo_registro.__dict__
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
    return [e.__dict__ for e in empleados]