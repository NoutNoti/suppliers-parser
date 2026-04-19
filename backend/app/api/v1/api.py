# import asyncio
# from fastapi import FastAPI, Query
# from fastapi.responses import JSONResponse
# import logging

# logging.basicConfig(level=logging.INFO)

# from app.suppliers.andopt2_com_ua.client import SupplierParserAndopt2
# from app.suppliers.dtopelectronic_com_ua.client import SupplierParserDtopelectronic
# from app.suppliers.grantopt_com_ua.client import SupplierParserGrantopt
# from app.suppliers.jmaxtvshop_com_ua.client import SupplierParserJmaxtvshop
# from app.suppliers.venera7km_com_ua.client import SupplierParserVenera7km
# from app.suppliers.melad_com_ua.client import SupplierParserMelad
# from app.suppliers.matrix7km_com.client import SupplierParserMatrix7km
# from app.suppliers.jumpex_com_ua.client import SupplierParserJumpex
# from app.suppliers.b2b_spartakelectronics_com.client import SupplierParserSpartak

# app = FastAPI(title="Supply Parser API")

# email1 = "ekzoololo@gmail.com"
# pass1 = "111111aA"
# pass2 = "0992350408aA"
# spartak_login = "3577"
# spartak_pass = "111111aA"

# @app.get("/suppliers/andopt2")
# async def parse_andopt2(
#     email: str = Query(default=email1),
#     password: str = Query(default=pass1),
# ):
#     async with SupplierParserAndopt2(email=email, password=password) as parser:
#         products = await parser.parse_all()
#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])



# @app.get("/suppliers/dtopelectronic")
# async def parse_dtopelectronic(
#     email: str = Query(default=email1),
#     password: str = Query(default=pass1),
# ):
#     async with SupplierParserDtopelectronic(email=email, password=password) as parser:
#         products = await parser.parse_all()
        
#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])

# # @app.get("/suppliers/dtopelectronic/get-stock")
# # async def get_stock_andopt2(
# #     email: str = Query(default=email1),
# #     password: str = Query(default=pass1),
# #     product_id:  str = Query(default=20661),
# # ):
# #     async with SupplierParserDtopelectronic(email=email, password=password) as parser:
# #         stock = await parser.get_stock_by_product_id(product_id=product_id)

# #     return JSONResponse(stock)


# @app.get("/suppliers/jmaxtvshop")
# async def parse_jmaxtvshop(
#     email: str = Query(default=email1),
#     password: str = Query(default=pass1),
# ):
#     async with SupplierParserJmaxtvshop(email=email, password=password) as parser:
#         products = await parser.parse_all()
        
#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])

# @app.get("/suppliers/venera7km")
# async def parse_venera7km(
#     email: str = Query(default=email1),
#     password: str = Query(default=pass1),
# ):
#     async with SupplierParserVenera7km(email=email, password=password) as parser:
#         products = await parser.parse_all()
        
#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])


# @app.get("/suppliers/grantopt")
# async def parse_grantopt(
#     email: str = Query(default=email1),
#     password: str = Query(default=pass1),
# ):
#     async with SupplierParserGrantopt(email=email, password=password) as parser:
#         products = await parser.parse_all()

#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])



# @app.get("/suppliers/melad")
# async def parse_melad(
#     email: str = Query(default=email1),
#     password: str = Query(default=pass2),
# ):
#     async with SupplierParserMelad(email=email, password=password) as parser:
#         products = await parser.parse_all()
#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])


# @app.get("/suppliers/matrix7km")
# async def parse_matrix7km(
#     email: str = Query(default=email1),
#     password: str = Query(default=pass1),
# ):
#     async with SupplierParserMatrix7km(email=email, password=password) as parser:
#         products = await parser.parse_all()
#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])


# @app.get("/suppliers/jumpex")
# async def parse_jumpex(
#     email: str = Query(default=email1),
#     password: str = Query(default=pass2),
# ):
#     async with SupplierParserJumpex(email=email, password=password) as parser:
#         products = await parser.parse_all()
#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])


# @app.get("/suppliers/spartak/categories")
# async def get_spartak_categories(
#     email: str = Query(default=spartak_login),
#     password: str = Query(default=spartak_pass),
# ):
#     async with SupplierParserSpartak(email=email, password=password) as parser:
#         categories = await parser._get_all_categories()
#     return JSONResponse(content=categories)


# @app.get("/categories")
# async def get_all_categories(
#     email: str = Query(default=email1),
#     password1: str = Query(default=pass1),
#     password2: str = Query(default=pass2),
# ):
#     suppliers = {
#         "andopt2":         (SupplierParserAndopt2, email, password1),
#         "dtopelectronic":  (SupplierParserDtopelectronic, email, password1),
#         "grantopt":        (SupplierParserGrantopt, email, password1),
#         "jmaxtvshop":      (SupplierParserJmaxtvshop, email, password1),
#         "venera7km":       (SupplierParserVenera7km, email, password1),
#         "melad":           (SupplierParserMelad, email, password2),
#         "matrix7km":       (SupplierParserMatrix7km, email, password1),
#         "jumpex":          (SupplierParserJumpex, email, password2),
#     }

#     async def fetch_categories(name, cls, em, pw):
#         try:
#             async with cls(email=em, password=pw) as parser:
#                 cats = await parser._get_all_categories(parser.PAGE_CONFIG.category_tag)
#             return name, cats
#         except Exception as e:
#             logging.error("[categories] %s error: %s", name, e)
#             return name, []

#     results = await asyncio.gather(
#         *[fetch_categories(n, cls, em, pw) for n, (cls, em, pw) in suppliers.items()]
#     )
#     return JSONResponse(content={name: cats for name, cats in results})


# @app.get("/suppliers/spartak")
# async def parse_spartak(
#     email: str = Query(default=spartak_login),
#     password: str = Query(default=spartak_pass),
# ):
#     async with SupplierParserSpartak(email=email, password=password) as parser:
#         products = await parser.parse_all()
#     return JSONResponse(content=[p.model_dump(mode="json") for p in products])
