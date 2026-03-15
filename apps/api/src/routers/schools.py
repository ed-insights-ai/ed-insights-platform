from fastapi import APIRouter

router = APIRouter(prefix="/api")

SCHOOLS = [
    {
        "id": "harding",
        "name": "Harding",
        "abbreviation": "HU",
        "conference": "GAC",
        "mascot": "Bisons",
    },
    {
        "id": "obu",
        "name": "Ouachita Baptist",
        "abbreviation": "OBU",
        "conference": "GAC",
        "mascot": "Tigers",
    },
]


@router.get("/schools")
async def list_schools():
    return SCHOOLS
