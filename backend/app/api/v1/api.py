import logging

from fastapi import (
    APIRouter,
    Query,
)
from fastapi.responses import (
    JSONResponse,
)

from app.suppliers.andopt2_com_ua.client import (
    SupplierAndopt2,
)
from app.suppliers.dtopelectronic_com_ua.client import (
    SupplierDtopelectronic,
)
from app.suppliers.jmaxtvshop_com_ua.client import (
    SupplierJmaxtvshop,
)
from app.suppliers.venera7km_com_ua.client import (
    SupplierVenera7km,
)
from app.suppliers.grantopt_com_ua.client import (
    SupplierGrantopt,
)
from app.suppliers.melad_com_ua.client import (
    SupplierMelad,
)
from app.suppliers.jumpex_com_ua.client import (
    SupplierJumpex,
)
from app.suppliers.matrix7km_com.client import (
    SupplierMatrix7km,
)
from app.suppliers.b2b_spartakelectronics_com.client import (
    SupplierSpartakB2B,
)

logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"],
)

EMAIL = "ekzoololo@gmail.com"
PASSWORD = "111111aA"
MELAD_PASSWORD = "0992350408aA"
JUMPEX_PASSWORD = "0992350408aA"
SPARTAK_LOGIN = "3577"


@router.get("/andopt2/products")
async def get_andopt2_products():
    async with SupplierAndopt2(
        email=EMAIL,
        password=PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])


@router.get("/dtopelectronic/products")
async def get_dtopelectronic_products():
    async with SupplierDtopelectronic(
        email=EMAIL,
        password=PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])


@router.get("/jmaxtvshop/products")
async def get_jmaxtvshop_products():
    async with SupplierJmaxtvshop(
        email=EMAIL,
        password=PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])


@router.get("/venera7km/products")
async def get_venera7km_products():
    async with SupplierVenera7km(
        email=EMAIL,
        password=PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])


@router.get("/grantopt/products")
async def get_grantopt_products():
    async with SupplierGrantopt(
        email=EMAIL,
        password=PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])


@router.get("/melad/products")
async def get_melad_products():
    async with SupplierMelad(
        email=EMAIL,
        password=MELAD_PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])


@router.get("/jumpex/products")
async def get_jumpex_products():
    async with SupplierJumpex(
        email=EMAIL,
        password=JUMPEX_PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])


@router.get("/matrix7km/products")
async def get_matrix7km_products():
    async with SupplierMatrix7km(
        email=EMAIL,
        password=PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])


@router.get("/spartak-b2b/products")
async def get_spartak_b2b_products():
    async with SupplierSpartakB2B(
        email=SPARTAK_LOGIN,
        password=PASSWORD,
    ) as parser:
        products = await parser.parse_all()
    return JSONResponse(content=[p.model_dump(mode="json") for p in products])
