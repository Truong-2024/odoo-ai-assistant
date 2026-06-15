# backend/app/repositories/odoo_repository.py
import os
import logging
from typing import List, Dict, Any, Optional
import odoorpc
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class OdooRepository:
    """
    Repository trung tâm kết nối với Odoo ERP
    """

    def __init__(self):
        self.odoo = None
        self.host = os.getenv("ODOO_HOST", "localhost")
        self.port = int(os.getenv("ODOO_PORT", 8069))
        self.db = os.getenv("ODOO_DB")
        self.user = os.getenv("ODOO_USER")
        self.password = os.getenv("ODOO_PASSWORD")
        self.connect()

    def connect(self):
        """Kết nối đến Odoo"""
        try:
            self.odoo = odoorpc.ODOO(host=self.host, port=self.port, timeout=120)
            self.odoo.login(db=self.db, login=self.user, password=self.password)
            
            logger.info(f"✅ Connected to Odoo | DB: {self.db} | User: {self.odoo.env.user.name}")
            if not hasattr(self, "_connected_printed"):
                print("✅ Kết nối Odoo thành công!")
                self._connected_printed = True
        except Exception as e:
            logger.error(f"❌ Odoo Connection Error: {e}")
            print(f"❌ Odoo Connection Error: {e}")
            raise

    # ==================== CORE METHODS ====================

    def search_read(
        self,
        model: str,
        domain: Optional[list] = None,
        fields: Optional[list] = None,
        limit: int = 100,
        order: Optional[str] = None
    ) -> List[Dict]:
        try:
            if domain is None:
                domain = []
            if fields is None:
                fields = []
            result = self.odoo.env[model].search_read(
                domain=domain,
                fields=fields,
                limit=limit,
                order=order
            )
            return result
        except Exception as e:
            logger.error(f"[search_read ERROR] Model={model} | {e}")
            return []

    def search(self, model: str, domain: Optional[list] = None, limit: int = 100) -> List[int]:
        try:
            if domain is None:
                domain = []
            return self.odoo.env[model].search(domain, limit=limit)
        except Exception as e:
            logger.error(f"[search ERROR] Model={model} | {e}")
            return []

    def read(self, model: str, ids: List[int], fields: Optional[list] = None) -> List[Dict]:
        try:
            if not ids:
                return []
            if fields is None:
                fields = []
            return self.odoo.env[model].read(ids, fields=fields)
        except Exception as e:
            logger.error(f"[read ERROR] Model={model} | {e}")
            return []

    def create(self, model: str, vals: Dict[str, Any]) -> int:
        try:
            record_id = self.odoo.env[model].create(vals)
            logger.info(f"✅ Created {model} | ID: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"[create ERROR] Model={model} | {e}")
            raise

    def write(self, model: str, record_id: int, vals: Dict[str, Any]) -> bool:
        try:
            result = self.odoo.env[model].browse(record_id).write(vals)
            logger.info(f"✅ Updated {model} | ID: {record_id}")
            return result
        except Exception as e:
            logger.error(f"[write ERROR] Model={model} | {e}")
            return False

    def unlink(self, model: str, record_id: int) -> bool:
        try:
            result = self.odoo.env[model].browse(record_id).unlink()
            logger.info(f"✅ Deleted {model} | ID: {record_id}")
            return result
        except Exception as e:
            logger.error(f"[unlink ERROR] Model={model} | {e}")
            return False