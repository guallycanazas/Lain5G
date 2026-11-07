from fastapi import APIRouter, Depends

from ..dependencies import get_sim_programmer_service, require_mutations_enabled
from ..models.sim_programmer import SimCardStatus, SimProgramRequest, SimProgramResult, SimProgrammerStatus, SimReaderRequest
from ..services.sim_programmer_service import SimProgrammerService

router = APIRouter(prefix="/api/sim-programmer", tags=["sim-programmer"])


@router.get("/status", response_model=SimProgrammerStatus)
def status(service: SimProgrammerService = Depends(get_sim_programmer_service)) -> SimProgrammerStatus:
    return SimProgrammerStatus(**service.status())


@router.post("/inspect", response_model=SimCardStatus)
def inspect(payload: SimReaderRequest, service: SimProgrammerService = Depends(get_sim_programmer_service)) -> SimCardStatus:
    return SimCardStatus(**service.inspect(payload.reader_index))


@router.post("/program", response_model=SimProgramResult, dependencies=[Depends(require_mutations_enabled)])
def program(payload: SimProgramRequest, service: SimProgrammerService = Depends(get_sim_programmer_service)) -> SimProgramResult:
    return SimProgramResult(**service.program(payload))
