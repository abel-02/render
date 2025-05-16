import psycopg2
from psycopg2 import pool  # Opcional para connection pooling
import os


# Cargar variables de entorno desde .env


class Database:
    # Configuración para Supabase (actualizada)
    _config = {
        "dbname": "database_labo",  # Nombre de la BD en Supabase (por defecto es 'postgres')
        "user": "database_labo_owner",    # Usuario por defecto en Supabase
        "password": "npg_T2tevF4uMhZB",  # Contraseña (DEBES configurarla en .env)
        "host": "ep-gentle-poetry-a48jtsf3-pooler.us-east-1.aws.neon.tech",  # Endpoint de Supabase
        "port": "5432",        # Puerto por defecto
        # Opcional: forzar SSL (recomendado para Supabase)

    }

    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        """Establece la conexión a la BD"""
        try:
            self.conn = psycopg2.connect(**self._config)
            print("✅ Conexión exitosa a Supabase PostgreSQL")
        except Exception as e:
            print(f"❌ Error al conectar: {e}")
            raise

    def get_cursor(self):
        """Devuelve un cursor para ejecutar queries"""
        if not self.conn or self.conn.closed:
            self.connect()  # Reconecta si la conexión está cerrada
        return self.conn.cursor()

    def close(self):
        """Cierra conexión y cursor"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            print("🔌 Conexión cerrada")

    # Método estático para connection pooling (opcional)
    @staticmethod
    def get_connection_pool(minconn=1, maxconn=10):
        return pool.SimpleConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            **Database._config
        )

# Instancia global (para uso en otros módulos)
db = Database()