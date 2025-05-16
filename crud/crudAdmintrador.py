from datetime import datetime, date, time
import psycopg2
from psycopg2 import sql
from .database import db


class AdminCRUD:
    @staticmethod
    def crear_empleado(numero_identificacion: str, nombre: str, apellido: str, tipo_identificacion: str,
                      fecha_nacimiento: date, correo_electronico: str, telefono: str, calle: str,
                      numero_calle: str, localidad: str, partido: str, genero: str, nacionalidad: str, estado_civil: str):
        """Registra un nuevo empleado con todos los campos"""
        try:
            with db.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO empleado (
                        nombre, apellido, tipo_identificacion, numero_identificacion,
                        fecha_nacimiento, correo_electronico, telefono, calle,
                        numero_calle, localidad, partido, genero, nacionalidad, estado_civil
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_empleado, numero_identificacion, nombre, apellido
                    """,
                    (
                        nombre, apellido, tipo_identificacion, numero_identificacion,
                        fecha_nacimiento, correo_electronico, telefono, calle,
                        numero_calle, localidad, partido, genero, nacionalidad, estado_civil
                    )
                )
                empleado = cur.fetchone()
                db.conn.commit()
                return {
                    "id_empleado": empleado[0],
                    "numero_identificacion": empleado[1],
                    "nombre": empleado[2],
                    "apellido": empleado[3]
                }
        except psycopg2.IntegrityError as e:
            db.conn.rollback()
            if "numero_identificacion" in str(e):
                raise ValueError("El número de identificación ya está registrado")
            raise ValueError(f"Error de integridad: {e}")
        except Exception as e:
            db.conn.rollback()
            raise Exception(f"Error al crear empleado: {e}")

    @staticmethod
    def obtener_empleados():
        """Lista todos los empleados con información básica"""
        with db.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_empleado, numero_identificacion, nombre, apellido, correo_electronico, telefono
                FROM empleado
                ORDER BY apellido, nombre
                """
            )
            return [
                {
                    "id_empleado": row[0],
                    "numero_identificacion": row[1],
                    "nombre": row[2],
                    "apellido": row[3],
                    "correo": row[4],
                    "telefono": row[5]
                }
                for row in cur.fetchall()
            ]

    @staticmethod
    def obtener_detalle_empleado(id_empleado: int):
        """Obtiene todos los datos de un empleado"""
        with db.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_empleado, nombre, apellido, tipo_identificacion, numero_identificacion,
                       fecha_nacimiento, correo_electronico, telefono, calle,
                       numero_calle, localidad, partido, genero, nacionalidad, estado_civil
                FROM empleado
                WHERE id_empleado = %s
                """,
                (id_empleado,)
            )
            result = cur.fetchone()
            if result:
                return {
                    "id_empleado": result[0],
                    "nombre": result[1],
                    "apellido": result[2],
                    "tipo_identificacion": result[3],
                    "numero_identificacion": result[4],
                    "fecha_nacimiento": result[5],
                    "correo_electronico": result[6],
                    "telefono": result[7],
                    "calle": result[8],
                    "numero_calle": result[9],
                    "localidad": result[10],
                    "partido": result[11],
                    "genero": result[12],
                    "nacionalidad": result[13],
                    "estado_civil": result[14]
                }
            return None

    @staticmethod
    def registrar_jornada_calendario(id_empleado: int, fecha: date, estado_jornada: str,
                                     hora_entrada: time = None, hora_salida: time = None,
                                     horas_trabajadas: int = None, horas_extras: int = None,
                                     descripcion: str = None):
        """Registra o actualiza una jornada en el calendario"""
        try:
            with db.conn.cursor() as cur:
                # Verificar si ya existe registro para esa fecha
                cur.execute(
                    "SELECT 1 FROM calendario WHERE id_empleado = %s AND fecha = %s",
                    (id_empleado, fecha)
                )
                existe = cur.fetchone()

                if existe:
                    # Actualizar registro existente
                    cur.execute(
                        """
                        UPDATE calendario SET
                            estado_jornada = %s,
                            hora_entrada = %s,
                            hora_salida = %s,
                            horas_trabajadas = %s,
                            horas_extras = %s,
                            descripcion = %s
                        WHERE id_empleado = %s AND fecha = %s
                        RETURNING id_asistencia
                        """,
                        (
                            estado_jornada, hora_entrada, hora_salida,
                            horas_trabajadas, horas_extras, descripcion,
                            id_empleado, fecha
                        )
                    )
                else:
                    # Insertar nuevo registro
                    cur.execute(
                        """
                        INSERT INTO calendario (
                            id_empleado, fecha, dia, estado_jornada,
                            hora_entrada, hora_salida, horas_trabajadas,
                            horas_extras, descripcion
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id_asistencia
                        """,
                        (
                            id_empleado, fecha, fecha.strftime("%A"),
                            estado_jornada, hora_entrada, hora_salida,
                            horas_trabajadas, horas_extras, descripcion
                        )
                    )

                db.conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            db.conn.rollback()
            raise Exception(f"Error al registrar jornada: {e}")

    @staticmethod
    def obtener_calendario_empleado(id_empleado: int, mes: int = None, año: int = None):
        """Obtiene el calendario laboral de un empleado"""
        query = """
            SELECT id_asistencia, fecha, dia, estado_jornada,
                   hora_entrada, hora_salida, horas_trabajadas,
                   horas_extras, descripcion
            FROM calendario
            WHERE id_empleado = %s
        """
        params = [id_empleado]

        if mes and año:
            query += " AND EXTRACT(MONTH FROM fecha) = %s AND EXTRACT(YEAR FROM fecha) = %s"
            params.extend([mes, año])

        query += " ORDER BY fecha DESC"

        with db.conn.cursor() as cur:
            cur.execute(query, params)
            return [
                {
                    "id_asistencia": row[0],
                    "fecha": row[1],
                    "dia": row[2],
                    "estado_jornada": row[3],
                    "hora_entrada": row[4].strftime("%H:%M") if row[4] else None,
                    "hora_salida": row[5].strftime("%H:%M") if row[5] else None,
                    "horas_trabajadas": row[6],
                    "horas_extras": row[7],
                    "descripcion": row[8]
                }
                for row in cur.fetchall()
            ]

    @staticmethod
    def buscar_empleado_por_numero_identificacion(numero_identificacion: str):
        """Busca un empleado por número de identificación"""
        with db.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_empleado, numero_identificacion, nombre, apellido, correo_electronico, telefono
                FROM empleado
                WHERE numero_identificacion = %s
                """,
                (numero_identificacion,)
            )
            result = cur.fetchone()
            if result:
                return {
                    "id_empleado": result[0],
                    "numero_identificacion": result[1],
                    "nombre": result[2],
                    "apellido": result[3],
                    "correo": result[4],
                    "telefono": result[5]
                }
            return None