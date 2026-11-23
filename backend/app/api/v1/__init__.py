from fastapi import APIRouter

from app.api.v1 import auth, brand, catalog, datasources, organizations, roles, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(roles.router)
api_router.include_router(users.router)
api_router.include_router(brand.public_router)
api_router.include_router(brand.admin_router)
api_router.include_router(datasources.router)
api_router.include_router(catalog.router)
