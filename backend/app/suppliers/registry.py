from dataclasses import dataclass
from typing import Type

from app.config.settings import settings
from app.suppliers.andopt2_com_ua.client import SupplierAndopt2
from app.suppliers.b2b_spartakelectronics_com.client import SupplierSpartakB2B
from app.suppliers.base import BaseSupplierParser
from app.suppliers.dtopelectronic_com_ua.client import SupplierDtopelectronic
from app.suppliers.grantopt_com_ua.client import SupplierGrantopt
from app.suppliers.jmaxtvshop_com_ua.client import SupplierJmaxtvshop
from app.suppliers.jumpex_com_ua.client import SupplierJumpex
from app.suppliers.matrix7km_com.client import SupplierMatrix7km
from app.suppliers.melad_com_ua.client import SupplierMelad
from app.suppliers.venera7km_com_ua.client import SupplierVenera7km


@dataclass
class SupplierEntry:
    parser_class: Type[BaseSupplierParser]
    email: str
    password: str

    @property
    def name(self) -> str:
        return self.parser_class.SUPPLIER_NAME

    def build(self) -> BaseSupplierParser:
        return self.parser_class(email=self.email, password=self.password)


SUPPLIERS: list[SupplierEntry] = [
    SupplierEntry(SupplierAndopt2, settings.SUPPLIER_EMAIL, settings.SUPPLIER_PASSWORD),
    SupplierEntry(
        SupplierDtopelectronic, settings.SUPPLIER_EMAIL, settings.SUPPLIER_PASSWORD
    ),
    SupplierEntry(
        SupplierJumpex, settings.SUPPLIER_EMAIL, settings.SUPPLIER_JUMPEX_PASSWORD
    ),
    SupplierEntry(
        SupplierMelad, settings.SUPPLIER_EMAIL, settings.SUPPLIER_MELAD_PASSWORD
    ),
    SupplierEntry(
        SupplierGrantopt, settings.SUPPLIER_EMAIL, settings.SUPPLIER_PASSWORD
    ),
    SupplierEntry(
        SupplierMatrix7km, settings.SUPPLIER_EMAIL, settings.SUPPLIER_PASSWORD
    ),
    SupplierEntry(
        SupplierSpartakB2B, settings.SUPPLIER_SPARTAK_LOGIN, settings.SUPPLIER_PASSWORD
    ),
    SupplierEntry(
        SupplierVenera7km, settings.SUPPLIER_EMAIL, settings.SUPPLIER_PASSWORD
    ),
    SupplierEntry(
        SupplierJmaxtvshop, settings.SUPPLIER_EMAIL, settings.SUPPLIER_PASSWORD
    ),
]
