from agrobr.constants import URLS, Fonte

GRAPHQL_URL: str = URLS[Fonte.MAPBIOMAS_ALERTA]["graphql"]

ALERTS_QUERY = """
query alerts(
  $page: Int, $limit: Int,
  $startDate: BaseDate, $endDate: BaseDate,
  $sources: [SourceTypes!],
  $boundingBox: [Float!],
  $territoryIds: [Int!]
) {
  alerts(
    page: $page, limit: $limit,
    startDate: $startDate, endDate: $endDate,
    sources: $sources,
    boundingBox: $boundingBox,
    territoryIds: $territoryIds
  ) {
    collection {
      alertCode
      areaHa
      detectedAt
      publishedAt
      statusName
      sources { name }
      coordenates { latitude longitude }
      geometryWkt
    }
    metadata {
      currentPage
      totalCount
      totalPages
    }
  }
}
"""

ALERT_DATE_RANGE_QUERY = """
{
  alertDateRange {
    minDetectedAt
    maxDetectedAt
    minPublishedAt
    maxPublishedAt
  }
}
"""

LAST_PUBLICATION_QUERY = """
{
  lastAlertPublication {
    publishedAt
    total
  }
}
"""

RENAME_MAP: dict[str, str] = {
    "alertCode": "alert_code",
    "areaHa": "area_ha",
    "detectedAt": "data_deteccao",
    "publishedAt": "data_publicacao",
    "statusName": "status",
}

COLUNAS_SAIDA: list[str] = [
    "alert_code",
    "area_ha",
    "data_deteccao",
    "data_publicacao",
    "status",
    "fonte",
    "lat",
    "lon",
]

COLUNAS_SAIDA_GEO: list[str] = COLUNAS_SAIDA + ["geometry"]
