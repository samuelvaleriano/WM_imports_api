from pydantic import BaseModel


class CEPResponse(BaseModel):
    cep: str
    logradouro: str
    complemento: str
    bairro: str
    localidade: str
    uf: str
