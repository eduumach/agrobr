from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.unica import parser
from agrobr.unica.models import COLUNAS_HISTORICO, COLUNAS_RESUMO, COLUNAS_SERIES

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "unica"


@pytest.fixture(scope="module")
def parsed_quinzenal() -> parser.ParsedQuinzenal:
    pdf_bytes = (GOLDEN_DIR / "relatorio_quinzenal.pdf").read_bytes()
    return parser.parse_quinzenal_pdf(pdf_bytes)


class TestTokenToFloat:
    def test_milhar_br_ponto_unico(self):
        assert parser._token_to_float("34.631") == 34631.0

    def test_milhar_br_multiplos_pontos(self):
        assert parser._token_to_float("8.253.154") == 8253154.0

    def test_decimal_virgula(self):
        assert parser._token_to_float("106,81") == 106.81

    def test_percentual(self):
        assert parser._token_to_float("74,58%") == 74.58

    def test_negativo(self):
        assert parser._token_to_float("-11,08%") == -11.08

    def test_zero(self):
        assert parser._token_to_float("0") == 0.0

    def test_nao_numerico_retorna_none(self):
        assert parser._token_to_float("n/a") is None
        assert parser._token_to_float("-") is None


class TestQuinzenaToDate:
    def test_inicio_de_safra(self):
        assert parser._quinzena_to_date("16/04", "2026/2027") == pd.Timestamp(2026, 4, 16)

    def test_meio_de_safra(self):
        assert parser._quinzena_to_date("01/12", "2026/2027") == pd.Timestamp(2026, 12, 1)

    def test_virada_de_ano(self):
        assert parser._quinzena_to_date("01/01", "2026/2027") == pd.Timestamp(2027, 1, 1)

    def test_fechamento_da_safra(self):
        assert parser._quinzena_to_date("01/04", "2026/2027") == pd.Timestamp(2027, 4, 1)


class TestParseQuinzenalGolden:
    def test_safra_e_posicao(self, parsed_quinzenal):
        assert parsed_quinzenal.safra == "2026/2027"
        assert parsed_quinzenal.posicao == pd.Timestamp(2026, 5, 1)

    def test_resumo_shape(self, parsed_quinzenal):
        resumo = parsed_quinzenal.resumo
        assert list(resumo.columns) == COLUNAS_RESUMO
        assert len(resumo) == 66
        assert resumo["produto"].nunique() == 11
        assert set(resumo["periodo"]) == {"acumulado", "quinzena"}
        assert set(resumo["regiao"]) == {"centro_sul", "sao_paulo", "demais_estados"}

    def test_resumo_valores_acumulado_centro_sul(self, parsed_quinzenal):
        cs = parsed_quinzenal.resumo.query("periodo == 'acumulado' and regiao == 'centro_sul'")
        valores = cs.set_index("produto")["valor"]
        assert valores["cana"] == 60458.0
        assert valores["acucar"] == 2475.0
        assert valores["etanol_total"] == 3288.0
        assert valores["atr_por_tonelada"] == 112.58
        assert valores["mix_acucar"] == 38.16

    def test_resumo_mix_sem_variacao(self, parsed_quinzenal):
        mix = parsed_quinzenal.resumo[
            parsed_quinzenal.resumo["produto"].isin(["mix_acucar", "mix_etanol"])
        ]
        assert mix["variacao_pct"].isna().all()

    def test_series_shape(self, parsed_quinzenal):
        series = parsed_quinzenal.series
        assert list(series.columns) == COLUNAS_SERIES
        assert len(series) == 30
        assert series["produto"].nunique() == 5
        assert set(series["quinzena"]) == {"16/04", "01/05"}

    def test_series_valores_cana_centro_sul(self, parsed_quinzenal):
        cana = parsed_quinzenal.series.query(
            "produto == 'cana' and regiao == 'centro_sul' and quinzena == '01/05'"
        )
        assert cana["valor"].iloc[0] == 60457836.0
        assert cana["valor_safra_anterior"].iloc[0] == 34631274.0
        assert cana["unidade"].iloc[0] == "t"

    def test_series_datas_inferidas(self, parsed_quinzenal):
        datas = set(parsed_quinzenal.series["data"])
        assert datas == {pd.Timestamp(2026, 4, 16), pd.Timestamp(2026, 5, 1)}

    def test_consistencia_resumo_vs_series(self, parsed_quinzenal):
        resumo_cana = parsed_quinzenal.resumo.query(
            "produto == 'cana' and periodo == 'acumulado' and regiao == 'centro_sul'"
        )["valor"].iloc[0]
        serie_cana = parsed_quinzenal.series.query(
            "produto == 'cana' and regiao == 'centro_sul' and quinzena == '01/05'"
        )["valor"].iloc[0]
        assert serie_cana / 1000 == pytest.approx(resumo_cana, rel=0.001)


class TestParseQuinzenalErros:
    def test_capa_sem_safra_raises(self):
        with pytest.raises(ParseError, match="Capa"):
            parser._parse_capa("texto qualquer sem padrao")

    def test_tabelas_ausentes_raises(self):
        with pytest.raises(ParseError, match="Tabelas ausentes"):
            parser._localizar_tabelas(["Tabela 1. titulo\nTabela 2. titulo"])

    def test_quinzena_com_tokens_incompletos_raises(self):
        paginas = dict.fromkeys(range(1, 8), "Tabela 3. moagem\n16/04 1.000 2.000 10%\nTabela 4.\n")
        paginas[3] = "Tabela 3. moagem\n16/04 1.000 2.000 10%\n"
        with pytest.raises(ParseError, match="esperado 9"):
            parser._parse_series(paginas, "2026/2027")

    def test_quinzena_com_token_nao_numerico_raises(self):
        linha = "16/04 1.000 2.000 10,5 1.000 abc 10,5 1.000 2.000 10,5"
        paginas = dict.fromkeys(range(1, 8), f"Tabela 3. moagem\n{linha}\nTabela 4.\n")
        paginas[3] = f"Tabela 3. moagem\n{linha}\n"
        with pytest.raises(ParseError, match="token não numérico"):
            parser._parse_series(paginas, "2026/2027")

    def test_resumo_com_valor_primario_nao_numerico_raises(self):
        linha = "Cana-de-açúcar 1.000 2.000 10,5 1.000 xyz 10,5 1.000 2.000 10,5"
        paginas = {1: f"Tabela 1. Posição da safra\n{linha}\n"}
        with pytest.raises(ParseError, match="valor não numérico"):
            parser._parse_resumo(paginas, "2026/2027")


class TestValidacaoSeries:
    def _df(self, produto: str, valor: float) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "data": pd.Timestamp(2026, 4, 16),
                    "quinzena": "16/04",
                    "safra": "2026/2027",
                    "produto": produto,
                    "regiao": "centro_sul",
                    "valor": valor,
                    "valor_safra_anterior": valor / 2,
                    "variacao_pct": 100.0,
                    "unidade": "t",
                }
            ]
        )

    def test_valor_negativo_raises(self):
        with pytest.raises(ParseError, match="negativos"):
            parser._validate_series(self._df("cana", -1.0))

    def test_moagem_acima_do_plausivel_raises(self):
        with pytest.raises(ParseError, match="acima do plausível"):
            parser._validate_series(self._df("cana", 800_000_000.0))

    def test_moagem_plausivel_passa(self):
        parser._validate_series(self._df("cana", 60_000_000.0))


class TestParseHistoricoGolden:
    def test_acucar_mil_toneladas(self):
        content = (GOLDEN_DIR / "hist_acucar.xlsx").read_bytes()
        df = parser.parse_historico_xlsx(content, "acucar")

        assert list(df.columns) == COLUNAS_HISTORICO
        assert len(df) == 81
        assert df["unidade"].eq("mil_t").all()
        assert df["localidade"].nunique() == 27
        sp = df.query("localidade == 'SP' and safra == '2020/2021'")
        assert sp["valor"].iloc[0] == pytest.approx(26324.147)

    def test_etanol_mil_m3(self):
        content = (GOLDEN_DIR / "hist_etanol_total.xlsx").read_bytes()
        df = parser.parse_historico_xlsx(content, "etanol_total")

        assert df["unidade"].eq("mil_m3").all()
        brasil = df.query("localidade == 'brasil' and safra == '2020/2021'")
        assert brasil["valor"].iloc[0] == pytest.approx(32503.0, rel=0.01)

    def test_agregados_presentes(self):
        content = (GOLDEN_DIR / "hist_acucar.xlsx").read_bytes()
        df = parser.parse_historico_xlsx(content, "acucar")

        assert {"centro_sul", "norte_nordeste", "brasil"} <= set(df["localidade"])
        assert "SP" in set(df["localidade"])


class TestParseHistoricoErros:
    def _xlsx(self, rows: list[list]) -> bytes:
        import io

        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def test_sem_unidade_raises(self):
        content = self._xlsx([["Estado/Safra", "2020/2021"], ["Acre", 0]])
        with pytest.raises(ParseError, match="Unidade"):
            parser.parse_historico_xlsx(content, "cana")

    def test_unidade_desconhecida_raises(self):
        content = self._xlsx([["Unidade: Sacas"], ["Estado/Safra", "2020/2021"], ["Acre", 0]])
        with pytest.raises(ParseError, match="Unidade desconhecida"):
            parser.parse_historico_xlsx(content, "cana")

    def test_sem_header_raises(self):
        content = self._xlsx([["Unidade: Mil toneladas"], ["Acre", 0]])
        with pytest.raises(ParseError, match="Estado/Safra"):
            parser.parse_historico_xlsx(content, "cana")

    def test_localidade_desconhecida_raises(self):
        content = self._xlsx(
            [
                ["Unidade: Mil toneladas"],
                ["Estado/Safra", "2020/2021"],
                ["Atlantida", 100],
            ]
        )
        with pytest.raises(ParseError, match="Localidade não reconhecida"):
            parser.parse_historico_xlsx(content, "cana")

    def test_valor_negativo_raises(self):
        content = self._xlsx(
            [
                ["Unidade: Mil toneladas"],
                ["Estado/Safra", "2020/2021"],
                ["Acre", -5],
            ]
        )
        with pytest.raises(ParseError, match="negativos"):
            parser.parse_historico_xlsx(content, "cana")
