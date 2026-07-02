"""엑셀 생성기 — 가공된 DataFrame → 지사별 다중 시트 + 서식 xlsx"""

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

INTERNAL_COLOR_COL = "_row_color"


def _safe_sheet_name(value: str) -> str:
    name = str(value)[:31]
    for ch in '/\\*[]:?':
        name = name.replace(ch, "_")
    return name or "시트"


def _hex(color: str) -> str:
    """'#FFFF00' → 'FFFF00' (openpyxl용). 빈 값이면 ''."""
    return color.lstrip("#").upper() if color else ""


def _apply_format(ws, colors: list[str], n_cols: int):
    """한 시트에 서식 적용. colors[i]는 데이터 i번째 행(엑셀 i+2행)의 배경색 헥사."""
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=n_cols):
        for cell in row:
            cell.alignment = center

    bold = Font(bold=True)
    header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
    for col in range(1, n_cols + 1):
        c = ws.cell(row=1, column=col)
        c.font = bold
        c.fill = header_fill

    for i, hexcolor in enumerate(colors):
        if not hexcolor:
            continue
        fill = PatternFill(start_color=hexcolor, end_color=hexcolor, fill_type="solid")
        for col in range(1, n_cols + 1):
            ws.cell(row=i + 2, column=col).fill = fill

    thin = Side(style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=n_cols):
        for cell in row:
            cell.border = border

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


def write_excel(df: pd.DataFrame, output_path: str, sheet_split_column: str = "") -> str:
    colors_all = (
        df[INTERNAL_COLOR_COL].fillna("").tolist()
        if INTERNAL_COLOR_COL in df.columns else [""] * len(df)
    )
    visible = df.drop(columns=[INTERNAL_COLOR_COL], errors="ignore")
    n_cols = len(visible.columns)

    split = sheet_split_column if sheet_split_column in visible.columns else ""

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # 메인 시트 (전체)
        visible.to_excel(writer, index=False, sheet_name="전체")

        sheet_colors = {"전체": [_hex(c) for c in colors_all]}

        if split:
            for value in sorted(visible[split].dropna().unique()):
                mask = (visible[split] == value).tolist()
                part = visible[visible[split] == value]
                part_colors = [_hex(c) for c, keep in zip(colors_all, mask) if keep]
                name = _safe_sheet_name(value)
                part.to_excel(writer, index=False, sheet_name=name)
                sheet_colors[name] = part_colors

        wb = writer.book
        for name, colors in sheet_colors.items():
            _apply_format(wb[name], colors, n_cols)

    return output_path
