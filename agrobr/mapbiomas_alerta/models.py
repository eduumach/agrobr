from agrobr.constants import URLS, Fonte

GRAPHQL_URL: str = URLS[Fonte.MAPBIOMAS_ALERTA]["graphql"]

SIGN_IN_MUTATION = """
mutation signIn($email: String!, $password: String!) {
  signIn(email: $email, password: $password) {
    token
  }
}
"""

ALERTS_QUERY = """
query alerts(
  $limit: Int, $offset: Int,
  $startDate: String, $endDate: String,
  $sources: [String!], $geometry: JSON
) {
  alerts(
    limit: $limit, offset: $offset,
    startDetectedAt: $startDate, endDetectedAt: $endDate,
    sources: $sources, territoryGeometry: $geometry
  ) {
    alertCode
    areaHa
    detectedAt
    publishedAt
    statusName
    source
    biome
    state
    city
    coordenates { lat lng }
    geometryWkt
  }
}
"""

ALERT_DATE_RANGE_QUERY = """
{
  alertDateRange {
    minDate
    maxDate
  }
}
"""

LAST_PUBLICATION_QUERY = """
{
  lastAlertPublication {
    date
    alertsCount
  }
}
"""

SOURCES_VALIDOS: frozenset[str] = frozenset({"DETER", "SAD", "GLAD", "SAD Caatinga"})

RENAME_MAP: dict[str, str] = {
    "alertCode": "alert_code",
    "areaHa": "area_ha",
    "detectedAt": "data_deteccao",
    "publishedAt": "data_publicacao",
    "statusName": "status",
    "source": "fonte",
    "biome": "bioma",
    "state": "uf",
    "city": "municipio",
}

COLUNAS_SAIDA: list[str] = [
    "alert_code",
    "area_ha",
    "data_deteccao",
    "data_publicacao",
    "status",
    "fonte",
    "bioma",
    "uf",
    "municipio",
    "lat",
    "lon",
]

COLUNAS_SAIDA_GEO: list[str] = COLUNAS_SAIDA + ["geometry"]
