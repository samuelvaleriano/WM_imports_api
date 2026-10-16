import json
import re
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.schemas.cep import CEPResponse

router = APIRouter(prefix="/cep", tags=["CEP"])


@router.get("/{cep}", response_model=CEPResponse)
def consultar_cep(cep: str) -> CEPResponse:
    if not re.fullmatch(r"\d{5}-?\d{3}", cep):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="CEP inválido. Informe 8 dígitos, com ou sem hífen.",
        )

    cep_limpo = cep.replace("-", "")
    request = Request(
        f"https://viacep.com.br/ws/{cep_limpo}/json/",
        headers={"User-Agent": "WM_Imports_API"},
    )

    try:
        with urlopen(request, timeout=5) as response:
            dados = json.loads(response.read())
    except HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O serviço ViaCEP retornou um erro.",
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível consultar o serviço ViaCEP.",
        ) from exc
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O serviço ViaCEP retornou uma resposta inválida.",
        ) from exc

    if not isinstance(dados, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O serviço ViaCEP retornou uma resposta inválida.",
        )

    if dados.get("erro") is True:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CEP não encontrado.",
        )

    try:
        return CEPResponse.model_validate(dados)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O serviço ViaCEP retornou dados de endereço inválidos.",
        ) from exc
