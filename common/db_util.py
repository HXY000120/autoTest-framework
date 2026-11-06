"""数据库工具：仅在被调用时连接，不强制依赖。"""
import pymysql


class DBUtil:
    def __init__(self, host, user, password, database, port: int = 3306, charset: str = "utf8mb4"):
        self.conn = pymysql.connect(
            host=host, user=user, password=password,
            database=database, port=port, charset=charset,
            autocommit=True,
        )

    def query(self, sql: str, args=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def execute(self, sql: str, args=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.rowcount

    def close(self):
        if self.conn:
            self.conn.close()
