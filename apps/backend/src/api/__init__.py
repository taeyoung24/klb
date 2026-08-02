from fastapi import APIRouter
from .leagues import router as leagues_router
from .clubs import router as clubs_router
from .standings import router as standings_router
from .matches import router as matches_router
from .system import router as system_router
from .worldview import router as worldview_router

router = APIRouter(prefix="/api")

router.include_router(leagues_router)
router.include_router(clubs_router)
router.include_router(standings_router)
router.include_router(matches_router)
router.include_router(system_router)
router.include_router(worldview_router)
