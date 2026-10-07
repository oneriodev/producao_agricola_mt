"""
Utilidades geográficas.

O Plotly (via d3) espera os polígonos em sentido HORÁRIO, enquanto o
padrão GeoJSON (RFC 7946), seguido pelo IBGE, usa ANTI-HORÁRIO. Sem
ajuste, o Plotly interpreta cada município como "o planeta inteiro menos
o município" e pinta o mapa todo.
"""

import copy

Anel = list[list[float]]  # lista de pontos [longitude, latitude]


def area_assinada(anel: Anel) -> float:
    """Área assinada pela fórmula do laço (shoelace).

    Positiva: sentido anti-horário. Negativa: sentido horário.
    Em GeoJSON o anel é fechado (último ponto = primeiro), então
    zip(anel, anel[1:]) percorre todos os lados.
    """
    soma = 0.0
    for p1, p2 in zip(anel, anel[1:]):
        soma += p1[0] * p2[1] - p2[0] * p1[1]
    return soma / 2


def _orientar_poligono(poligono: list[Anel]) -> list[Anel]:
    """Contorno externo (1º anel) em horário; buracos em anti-horário."""
    resultado = []
    for i, anel in enumerate(poligono):
        deve_ser_horario = i == 0             # só o 1º anel é o contorno externo
        eh_horario = area_assinada(anel) < 0
        if eh_horario != deve_ser_horario:    # sentido errado -> inverte
            anel = anel[::-1]
        resultado.append(anel)
    return resultado


def orientar_para_plotly(geojson: dict) -> dict:
    """Devolve uma CÓPIA do GeoJSON com os polígonos no sentido do Plotly."""
    novo = copy.deepcopy(geojson)  # não altera o original
    for feature in novo["features"]:
        geometria = feature["geometry"]
        if geometria["type"] == "Polygon":
            geometria["coordinates"] = _orientar_poligono(geometria["coordinates"])
        elif geometria["type"] == "MultiPolygon":
            # MultiPolygon = município com mais de uma parte (ex.: ilhas)
            geometria["coordinates"] = [
                _orientar_poligono(p) for p in geometria["coordinates"]
            ]
    return novo