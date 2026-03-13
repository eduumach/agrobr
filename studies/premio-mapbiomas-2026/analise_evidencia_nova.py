#!/usr/bin/env python3
"""
Análise de evidência nova para submissão ao Prêmio MapBiomas "Combate ao Desmatamento".

Peça 1: Correlação Spearman — DETER km² × gap % para TODOS os municípios de RO com soja
Peça 2: Distribuição de classes — Porto Velho & Vilhena (o que MapBiomas classifica no lugar de soja)

Fontes de dados (via agrobr v0.12.0):
  - IBGE PAM 2024 (colheita municipal de soja)
  - MapBiomas Collection 10 2024 (cobertura municipal)
  - DETER 2022–2025 (alertas de desmatamento, Amazônia)

Todas as funções são async; usamos asyncio.run() para chamá-las.
"""

from __future__ import annotations

import asyncio
import io
import os
import sys
import unicodedata
from pathlib import Path
from typing import Any

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding != "utf-8":
    assert isinstance(sys.stdout, io.TextIOWrapper)
    sys.stdout.reconfigure(encoding="utf-8")
    assert isinstance(sys.stderr, io.TextIOWrapper)
    sys.stderr.reconfigure(encoding="utf-8")

import pandas as pd
from scipy import stats

# ── Auxiliares ────────────────────────────────────────────────────────


def normalize_name(name: str) -> str:
    """Normaliza nome de município para join: minúsculo, sem acentos, sem sufixo de UF."""
    s = name.strip().lower()
    if " - " in s:
        s = s.rsplit(" - ", 1)[0].strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def fmt_ha(val: float) -> str:
    return f"{val:,.0f}".replace(",", ".")


# ── Coleta de Dados ──────────────────────────────────────────────────


async def fetch_ibge_pam_ro() -> pd.DataFrame:
    """IBGE PAM soja municipal RO 2024."""
    from agrobr.datasets import producao_anual

    print("  Buscando IBGE PAM soja RO 2024 (municipal)...")
    result = await producao_anual("soja", nivel="municipio", uf="RO", ano=2024)
    df: pd.DataFrame = result if isinstance(result, pd.DataFrame) else result[0]
    print(f"  → {len(df)} linhas, colunas: {df.columns.tolist()}")
    if len(df) > 0:
        print(f"  → Amostra:\n{df.head(3).to_string()}")
    return df


async def fetch_mapbiomas_ro() -> pd.DataFrame:
    """MapBiomas cobertura municipal RO 2024 (classes 39 + 41)."""
    from agrobr.mapbiomas import cobertura

    print("  Buscando MapBiomas cobertura municipal RO 2024 (~660MB na primeira vez)...")
    df = await cobertura(nivel="municipio", estado="RO", ano=2024)
    print(f"  → {len(df)} linhas, colunas: {df.columns.tolist()}")
    if len(df) > 0:
        print(f"  → Classes disponíveis: {sorted(df['classe_id'].unique().tolist())}")
    return df


async def fetch_deter_ro() -> pd.DataFrame:
    """Alertas DETER RO 2022–2025."""
    from agrobr.desmatamento import deter

    print("  Buscando DETER Amazônia RO 2022-2025...")
    df = await deter(uf="RO", data_inicio="2022-01-01")
    print(f"  → {len(df)} linhas, colunas: {df.columns.tolist()}")
    return df


# ── Análise ──────────────────────────────────────────────────────────


def build_merged_dataset(
    ibge_df: pd.DataFrame,
    mb_df: pd.DataFrame,
    deter_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join IBGE PAM × MapBiomas × DETER por nome de município.
    Retorna DataFrame com: municipio, ibge_ha, mb_ha, gap_pct, deter_km2
    """
    # ── IBGE: extrair area_colhida por município ──
    ibge = ibge_df.copy()
    mun_col = "localidade" if "localidade" in ibge.columns else "municipio"
    ibge["mun_norm"] = ibge[mun_col].apply(normalize_name)
    area_col = "area_colhida" if "area_colhida" in ibge.columns else "valor"
    ibge_agg = ibge.groupby("mun_norm")[area_col].sum().reset_index()
    ibge_agg.columns = ["mun_norm", "ibge_ha"]
    ibge_agg["ibge_ha"] = pd.to_numeric(ibge_agg["ibge_ha"], errors="coerce")

    name_map = ibge.drop_duplicates("mun_norm").set_index("mun_norm")[mun_col].to_dict()

    # ── MapBiomas: somar classes 39 (Soja) + 41 (OLT) por município ──
    mb = mb_df.copy()
    mb_soja = mb[mb["classe_id"].isin([39, 41])].copy()
    mb_soja["mun_norm"] = mb_soja["municipio"].apply(normalize_name)
    mb_agg = mb_soja.groupby("mun_norm")["area_ha"].sum().reset_index()
    mb_agg.columns = ["mun_norm", "mb_ha"]

    # ── DETER: agregar area_km2 por município ──
    det = deter_df.copy()
    det["mun_norm"] = det["municipio"].apply(normalize_name)
    det_agg = det.groupby("mun_norm")["area_km2"].sum().reset_index()
    det_agg.columns = ["mun_norm", "deter_km2"]

    # ── Join ──
    merged = ibge_agg.merge(mb_agg, on="mun_norm", how="inner")
    merged = merged.merge(det_agg, on="mun_norm", how="left")
    merged["deter_km2"] = merged["deter_km2"].fillna(0)

    merged["gap_pct"] = (merged["ibge_ha"] - merged["mb_ha"]) / merged["mb_ha"] * 100

    merged["municipio"] = merged["mun_norm"].map(name_map).fillna(merged["mun_norm"])

    merged = merged[(merged["ibge_ha"] > 0) & (merged["mb_ha"] > 0)].copy()
    merged = merged.sort_values("deter_km2", ascending=False).reset_index(drop=True)

    return merged[["municipio", "ibge_ha", "mb_ha", "gap_pct", "deter_km2"]]


def run_spearman(merged: pd.DataFrame) -> dict[str, Any]:
    """
    Correlação Spearman + Pearson: deter_km2 × gap_pct.
    Retorna dict com resultados para TODOS os municípios e SEM Porto Velho.
    """
    results = {}

    n = len(merged)
    if n < 5:
        print(f"\n  ⚠ Apenas {n} municípios — insuficiente para correlação")
        return {"n": n, "status": "insufficient_data"}

    rho, p_rho = stats.spearmanr(merged["deter_km2"], merged["gap_pct"])
    r, p_r = stats.pearsonr(merged["deter_km2"], merged["gap_pct"])
    results["all"] = {"n": n, "rho": rho, "p_rho": p_rho, "r": r, "p_r": p_r}

    pv_mask = merged["municipio"].apply(normalize_name).str.contains("porto velho")
    merged_no_pv = merged[~pv_mask]
    n2 = len(merged_no_pv)
    if n2 >= 5:
        rho2, p2 = stats.spearmanr(merged_no_pv["deter_km2"], merged_no_pv["gap_pct"])
        r2, p2_r = stats.pearsonr(merged_no_pv["deter_km2"], merged_no_pv["gap_pct"])
        results["no_pv"] = {"n": n2, "rho": rho2, "p_rho": p2, "r": r2, "p_r": p2_r}

    return results


def analyze_classes(mb_df: pd.DataFrame, municipio_name: str) -> pd.DataFrame:
    """
    Mostra todas as classes MapBiomas para um dado município.
    Retorna DataFrame ordenado por área decrescente.
    """
    mb = mb_df.copy()
    mb["mun_norm"] = mb["municipio"].apply(normalize_name)
    target = normalize_name(municipio_name)
    mun_data = mb[mb["mun_norm"].str.contains(target)]

    if mun_data.empty:
        print(f"  ⚠ Nenhum dado encontrado para '{municipio_name}'")
        return pd.DataFrame()

    classes = mun_data.groupby(["classe_id", "classe"])["area_ha"].sum().reset_index()
    classes = classes.sort_values("area_ha", ascending=False).reset_index(drop=True)
    return classes


# ── Saída ────────────────────────────────────────────────────────────


def print_separator(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_spearman_results(results: dict[str, Any]) -> None:
    print_separator("CORRELAÇÃO SPEARMAN: DETER km² × Gap %")

    if results.get("status") == "insufficient_data":
        print(f"  DADOS INSUFICIENTES (n={results['n']}). Abortando Spearman.")
        return

    all_r = results["all"]
    print(f"  TODOS OS MUNICÍPIOS (n={all_r['n']}):")
    print(f"    Spearman ρ = {all_r['rho']:.4f}  (p = {all_r['p_rho']:.4f})")
    print(f"    Pearson  r = {all_r['r']:.4f}  (p = {all_r['p_r']:.4f})")

    if "no_pv" in results:
        no_pv = results["no_pv"]
        print(f"\n  SEM PORTO VELHO (n={no_pv['n']}):")
        print(f"    Spearman ρ = {no_pv['rho']:.4f}  (p = {no_pv['p_rho']:.4f})")
        print(f"    Pearson  r = {no_pv['r']:.4f}  (p = {no_pv['p_r']:.4f})")

    rho_all = all_r["rho"]
    p_all = all_r["p_rho"]
    rho_no_pv = results.get("no_pv", {}).get("rho", 0)
    p_no_pv = results.get("no_pv", {}).get("p_rho", 1)

    print("\n  CRITÉRIOS GO/NO-GO:")
    if rho_all > 0.4 and p_all < 0.05:
        print(f"  ✓ ρ={rho_all:.3f} > 0.4, p={p_all:.4f} < 0.05 → GO (incluir)")
        if rho_no_pv > 0.3 and p_no_pv < 0.05:
            print(f"  ✓ Sem PV: ρ={rho_no_pv:.3f} > 0.3 → linguagem FORTE ok")
        else:
            print(f"  ~ Sem PV: ρ={rho_no_pv:.3f}, p={p_no_pv:.4f} → linguagem cautelosa")
    elif rho_all > 0.3 and p_all < 0.05:
        print(f"  ~ ρ={rho_all:.3f} > 0.3, p={p_all:.4f} < 0.05 → GO MARGINAL")
    else:
        print(f"  ✗ ρ={rho_all:.3f}, p={p_all:.4f} → NO-GO (não incluir)")


def print_class_distribution(classes_df: pd.DataFrame, mun_name: str, ibge_ha: float) -> None:
    print_separator(f"DISTRIBUIÇÃO DE CLASSES: {mun_name}")

    if classes_df.empty:
        print("  Sem dados disponíveis.")
        return

    KEY_CLASSES = {
        39: "Soja",
        41: "OLT",
        15: "Pastagem",
        21: "Mosaico Agr/Past",
        3: "Formação Florestal",
        4: "Formação Savânica",
        12: "Formação Campestre",
        9: "Silvicultura",
        24: "Área Urbanizada",
        25: "Outra Área Não Vegetada",
    }

    soja_olt = classes_df[classes_df["classe_id"].isin([39, 41])]["area_ha"].sum()

    print(f"  IBGE PAM soja: {fmt_ha(ibge_ha)} ha")
    print(f"  MapBiomas Soja+OLT: {fmt_ha(soja_olt)} ha")
    print(f"  Gap: {fmt_ha(ibge_ha - soja_olt)} ha ({(ibge_ha - soja_olt) / soja_olt * 100:+.0f}%)")
    print()

    print(f"  {'ID Classe':<12} {'Classe':<30} {'Área (ha)':>15} {'%':>8}")
    print(f"  {'-' * 12} {'-' * 30} {'-' * 15} {'-' * 8}")
    total = classes_df["area_ha"].sum()
    for _, row in classes_df.head(15).iterrows():
        cid = int(row["classe_id"])
        name = row["classe"] if pd.notna(row["classe"]) else KEY_CLASSES.get(cid, "?")
        area = row["area_ha"]
        pct = area / total * 100
        marker = " ← SOJA" if cid == 39 else (" ← OLT" if cid == 41 else "")
        print(f"  {cid:<12} {name:<30} {fmt_ha(area):>15} {pct:>7.1f}%{marker}")


def save_scatter_data(merged: pd.DataFrame, results: dict[str, Any], out_dir: Path) -> None:
    """Salva dados para geração do scatter plot."""
    csv_path = out_dir / "spearman_data.csv"
    export = merged.copy()
    export["ibge_ha"] = export["ibge_ha"].round(0).astype(int)
    export["mb_ha"] = export["mb_ha"].round(1)
    export["gap_pct"] = export["gap_pct"].round(1)
    export["deter_km2"] = export["deter_km2"].round(1)
    export["municipio"] = export["municipio"].str.replace(r"\s*-\s*RO$", "", regex=True)
    export.to_csv(csv_path, index=False, encoding="utf-8-sig", sep=";")
    print(f"\n  Dados do scatter salvos em: {csv_path.name}")

    summary_path = out_dir / "evidencia_nova_resultados.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("RESULTADOS — Evidência Nova (analise_evidencia_nova.py)\n")
        f.write("=" * 60 + "\n\n")

        if results.get("status") == "insufficient_data":
            f.write(f"SPEARMAN: dados insuficientes (n={results['n']})\n")
        else:
            all_r = results["all"]
            f.write(f"SPEARMAN — TODOS (n={all_r['n']}):\n")
            f.write(f"  ρ = {all_r['rho']:.4f}, p = {all_r['p_rho']:.4f}\n")
            f.write(f"  r = {all_r['r']:.4f}, p = {all_r['p_r']:.4f}\n\n")
            if "no_pv" in results:
                no_pv = results["no_pv"]
                f.write(f"SPEARMAN — SEM PORTO VELHO (n={no_pv['n']}):\n")
                f.write(f"  ρ = {no_pv['rho']:.4f}, p = {no_pv['p_rho']:.4f}\n")
                f.write(f"  r = {no_pv['r']:.4f}, p = {no_pv['p_r']:.4f}\n\n")

        f.write("\nDATASET CONSOLIDADO:\n")
        f.write(merged.to_string(index=False))
        f.write("\n")

    print(f"  Resumo salvo em: {summary_path.name}")


# ── Main ─────────────────────────────────────────────────────────────


async def main() -> None:
    out_dir = Path(__file__).parent

    print_separator("FASE 1: COLETA DE DADOS")

    ibge_df = await fetch_ibge_pam_ro()
    mb_df = await fetch_mapbiomas_ro()
    deter_df = await fetch_deter_ro()

    # ── Peça 1: Correlação Spearman ──
    print_separator("FASE 2: CORRELAÇÃO SPEARMAN")
    merged = build_merged_dataset(ibge_df, mb_df, deter_df)

    print(f"  Dataset consolidado: {len(merged)} municípios com soja em IBGE e MapBiomas\n")
    print(merged.to_string(index=False))

    spearman_results = run_spearman(merged)
    print_spearman_results(spearman_results)

    # ── Peça 2: Distribuição de Classes ──
    pv_ibge = merged.loc[
        merged["municipio"].apply(normalize_name).str.contains("porto velho"), "ibge_ha"
    ]
    pv_ibge_ha = pv_ibge.values[0] if len(pv_ibge) > 0 else 47_200

    pv_classes = analyze_classes(mb_df, "Porto Velho")
    print_class_distribution(pv_classes, "Porto Velho", pv_ibge_ha)

    vil_ibge = merged.loc[
        merged["municipio"].apply(normalize_name).str.contains("vilhena"), "ibge_ha"
    ]
    vil_ibge_ha = vil_ibge.values[0] if len(vil_ibge) > 0 else 85_400

    vil_classes = analyze_classes(mb_df, "Vilhena")
    print_class_distribution(vil_classes, "Vilhena", vil_ibge_ha)

    # ── Salvar saídas ──
    save_scatter_data(merged, spearman_results, out_dir)

    print_separator("CONCLUÍDO")
    print("  Próximos passos:")
    print("  1. Avaliar go/no-go com base nos resultados Spearman acima")
    print("  2. Se GO: gerar fig_5_spearman_scatter.png via gerar_graficos_pdf.py")
    print("  3. Atualizar submissao_combate_desmatamento.md com novos parágrafos")
    print("  4. Regenerar PDF via build_pdf.py")


if __name__ == "__main__":
    asyncio.run(main())
