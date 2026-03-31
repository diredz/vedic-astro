"""
Professional Vedic Astrology Report — PDF Export
Elegant cream/ink/gold theme. Print-ready.
"""
import io, re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Flowable
)
from reportlab.lib.styles import ParagraphStyle

W, H = A4
ML, MR, MT, MB = 20*mm, 20*mm, 22*mm, 22*mm

# ── Palette ──────────────────────────────────────────────────────────────────
CREAM      = colors.HexColor('#faf6ee')
CREAM2     = colors.HexColor('#f2ead8')
CREAM3     = colors.HexColor('#e8dfc8')
INK        = colors.HexColor('#1a1408')
INK2       = colors.HexColor('#2e2510')
INK3       = colors.HexColor('#4a3e28')
GOLD       = colors.HexColor('#9a6f20')
GOLD2      = colors.HexColor('#c49a38')
GOLD3      = colors.HexColor('#e8c96a')
GOLD_LITE  = colors.HexColor('#f5e9c0')
RED        = colors.HexColor('#8b2020')
TEAL       = colors.HexColor('#1a5c52')
BORDER     = colors.HexColor('#c8b480')
BORDER2    = colors.HexColor('#e0d0a8')
ROW_ODD    = colors.HexColor('#faf6ee')
ROW_EVEN   = colors.HexColor('#f4edd8')
HEAD_BG    = colors.HexColor('#2e2510')
HEAD_FG    = colors.HexColor('#f5e9c0')

PCOLS = {
    'Sun':     colors.HexColor('#b85c00'),
    'Moon':    colors.HexColor('#1a4a7a'),
    'Mars':    colors.HexColor('#8b1a1a'),
    'Mercury': colors.HexColor('#1a6b35'),
    'Jupiter': colors.HexColor('#7a5c00'),
    'Venus':   colors.HexColor('#7a1a5c'),
    'Saturn':  colors.HexColor('#3a2a6b'),
    'Rahu':    colors.HexColor('#3a3a3a'),
    'Ketu':    colors.HexColor('#5c4020'),
}

SIGN_ABBR   = ['','Ari','Tau','Gem','Can','Leo','Vir','Lib','Sco','Sag','Cap','Aqu','Pis']
HOUSE_NAMES = ['','Tanu','Dhana','Sahaja','Sukha','Putra','Shatru',
               'Kalatra','Mrityu','Dharma','Karma','Labha','Vyaya']
SI_POS = {
    1:(0,1), 2:(0,2), 3:(0,3), 4:(1,3), 5:(2,3), 6:(3,3),
    7:(3,2), 8:(3,1), 9:(3,0), 10:(2,0),11:(1,0),12:(0,0)
}


# ── Text cleaner ─────────────────────────────────────────────────────────────
def clean(t: str) -> str:
    t = re.sub(r'\[/?[a-zA-Z0-9_ ]+\]', '', t)
    t = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', t)
    t = re.sub(r'[─━╌┄╍═║╠╣╦╩╬│╭╮╰╯┌┐└┘├┤┬┴┼▀▄█▌▐░▒▓]', '', t)
    t = re.sub(r'[\U00010000-\U0010ffff]', '', t)
    t = re.sub(r'[^\x00-\xFF]', '', t)
    t = t.replace('\u2011','-').replace('\u2013','-').replace('\u2014','--')
    t = t.replace('\u2018',"'").replace('\u2019',"'")
    t = t.replace('\u201C','"').replace('\u201D','"')
    t = t.replace('\u2022','-').replace('\u00B7','-').replace('\u2026','...')
    t = t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    return t.strip()


# ── Styles ───────────────────────────────────────────────────────────────────
def _styles():
    def ps(name, **kw): return ParagraphStyle(name, **kw)
    return {
        'cover_name': ps('cn', fontSize=26, textColor=INK, fontName='Times-Bold',
                         alignment=TA_CENTER, spaceAfter=4, leading=32),
        'cover_sub':  ps('cs', fontSize=11, textColor=GOLD, fontName='Times-Italic',
                         alignment=TA_CENTER, spaceAfter=2),
        'cover_meta': ps('cm', fontSize=9, textColor=INK3, fontName='Helvetica',
                         alignment=TA_CENTER, spaceAfter=2),
        'section':    ps('sec', fontSize=10, textColor=HEAD_BG, fontName='Times-Bold',
                         spaceBefore=10, spaceAfter=4, leading=13),
        'body':       ps('body', fontSize=9, textColor=INK2, fontName='Times-Roman',
                         leading=14, spaceAfter=3, alignment=TA_JUSTIFY),
        'body_small': ps('bs', fontSize=8, textColor=INK3, fontName='Helvetica',
                         leading=11, spaceAfter=2),
        'pred_h':     ps('ph', fontSize=9.5, textColor=GOLD, fontName='Times-Bold',
                         spaceBefore=7, spaceAfter=2, leading=12),
        'pred_body':  ps('pb', fontSize=9, textColor=INK2, fontName='Times-Roman',
                         leading=15, spaceAfter=4, alignment=TA_JUSTIFY),
        'footer':     ps('ft', fontSize=7, textColor=INK3, fontName='Helvetica',
                         alignment=TA_CENTER),
        'table_hdr':  ps('th', fontSize=7.5, textColor=HEAD_FG, fontName='Helvetica-Bold'),
        'table_cell': ps('tc', fontSize=8, textColor=INK2, fontName='Helvetica', leading=11),
        'table_bold': ps('tb', fontSize=8, textColor=INK, fontName='Helvetica-Bold', leading=11),
    }


# ── Page background ───────────────────────────────────────────────────────────
def _page_bg(canvas, doc, name, dob_str):
    canvas.saveState()

    # Cream page
    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, W, H, stroke=0, fill=1)

    # Top header band
    canvas.setFillColor(HEAD_BG)
    canvas.rect(0, H-10*mm, W, 10*mm, stroke=0, fill=1)
    canvas.setFillColor(GOLD2)
    canvas.rect(0, H-10*mm-1.5, W, 2, stroke=0, fill=1)

    # Bottom footer band
    canvas.setFillColor(HEAD_BG)
    canvas.rect(0, 0, W, 8*mm, stroke=0, fill=1)
    canvas.setFillColor(GOLD2)
    canvas.rect(0, 8*mm, W, 2, stroke=0, fill=1)

    # Header text
    canvas.setFont('Helvetica-Bold', 7.5)
    canvas.setFillColor(GOLD3)
    canvas.drawString(ML, H-6.5*mm, name.upper())
    canvas.drawRightString(W-MR, H-6.5*mm, 'VEDIC HOROSCOPE  |  JYOTISH REPORT')

    # Footer text
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(GOLD3)
    canvas.drawCentredString(W/2, 3*mm, f'Page {doc.page}')
    canvas.drawString(ML, 3*mm, dob_str)
    canvas.drawRightString(W-MR, 3*mm, 'Lahiri Ayanamsa  |  Swiss Ephemeris')

    # Thin side rules
    canvas.setStrokeColor(BORDER2)
    canvas.setLineWidth(0.3)
    canvas.line(ML-5, MT+2*mm, ML-5, H-MT-2*mm)
    canvas.line(W-MR+5, MT+2*mm, W-MR+5, H-MT-2*mm)

    canvas.restoreState()


# ── South Indian Chart ────────────────────────────────────────────────────────
class SIChart(Flowable):
    def __init__(self, kundali, size=180):
        super().__init__()
        self.k = kundali
        self.sz = size
        self.width = size
        self.height = size

    def draw(self):
        c    = self.canv
        sz   = self.sz
        cell = sz / 4
        lagna = self.k['lagna']['sign_num']

        # Build sign→planet map
        sp = {i: [] for i in range(1, 13)}
        for pname, pd in self.k['planets'].items():
            label = pname + ('(R)' if pd.get('retrograde') else '')
            sp[pd['sign_num']].append(label)

        # Outer border (double line effect)
        c.setFillColor(CREAM2)
        c.rect(0, 0, sz, sz, stroke=0, fill=1)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        c.rect(0, 0, sz, sz, stroke=1, fill=0)
        c.setStrokeColor(GOLD2)
        c.setLineWidth(0.4)
        c.rect(2, 2, sz-4, sz-4, stroke=1, fill=0)

        # Inner grid
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        for x in [cell, cell*2, cell*3]:
            c.line(x, 0, x, sz)
        for y in [cell, cell*2, cell*3]:
            c.line(0, y, sz, y)

        for sn in range(1, 13):
            row, col = SI_POS[sn]
            cx = col * cell
            cy = sz - (row + 1) * cell

            is_lagna = (sn == lagna)
            house    = ((sn - lagna + 12) % 12) + 1

            # Cell fill
            fill_color = GOLD_LITE if is_lagna else (ROW_ODD if (row+col)%2==0 else ROW_EVEN)
            c.setFillColor(fill_color)
            c.rect(cx+1, cy+1, cell-2, cell-2, stroke=0, fill=1)

            # Lagna corner accent
            if is_lagna:
                c.setStrokeColor(GOLD)
                c.setLineWidth(1.2)
                c.line(cx+3, cy+cell-3, cx+18, cy+cell-3)
                c.line(cx+3, cy+cell-3, cx+3,  cy+cell-18)
                c.setLineWidth(0.5)
                c.line(cx+5, cy+cell-5, cx+14, cy+cell-5)
                c.line(cx+5, cy+cell-5, cx+5,  cy+cell-14)

            # Sign abbreviation
            c.setFont('Helvetica-Bold' if is_lagna else 'Helvetica', 6.5)
            c.setFillColor(GOLD if is_lagna else GOLD2)
            c.drawString(cx+4, cy+cell-11, SIGN_ABBR[sn])

            # House number
            c.setFont('Helvetica', 6)
            c.setFillColor(INK3)
            c.drawRightString(cx+cell-3, cy+cell-11, f'H{house}')

            # Planets
            planets = sp.get(sn, [])
            lh = 10.5
            start_y = cy + cell - 24
            for i, pl in enumerate(planets):
                ty = start_y - i * lh
                if ty < cy + 4: break
                base  = pl.replace('(R)', '')
                retro = pl.endswith('(R)')
                c.setFillColor(PCOLS.get(base, INK2))
                c.setFont('Helvetica-Bold' if is_lagna else 'Helvetica', 7.5)
                c.drawCentredString(cx+cell/2, ty, base + ('(R)' if retro else ''))

        # Center box
        c.setFillColor(HEAD_BG)
        c.rect(cell, cell, cell*2, cell*2, stroke=0, fill=1)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.rect(cell, cell, cell*2, cell*2, stroke=1, fill=0)
        c.setStrokeColor(GOLD2)
        c.setLineWidth(0.3)
        c.rect(cell+3, cell+3, cell*2-6, cell*2-6, stroke=1, fill=0)

        mx = cell*2
        my = cell*2
        c.setFont('Times-Bold', 9)
        c.setFillColor(GOLD3)
        c.drawCentredString(mx, my+16, 'KUNDALI')
        c.setFont('Helvetica', 7)
        c.setFillColor(GOLD2)
        c.drawCentredString(mx, my+5,   self.k['lagna']['sign'])
        c.setFillColor(colors.HexColor('#8a7050'))
        c.drawCentredString(mx, my-6,  'Moon: '+self.k['moon_sign'])
        c.drawCentredString(mx, my-16, self.k['moon_nakshatra'])
        c.drawCentredString(mx, my-26, 'Sun: '+self.k['sun_sign'])


# ── Helpers ───────────────────────────────────────────────────────────────────
def _divider(ST):
    return KeepTogether([
        Spacer(1, 4),
        HRFlowable(width='100%', thickness=1.0, color=GOLD2, spaceAfter=0),
        HRFlowable(width='100%', thickness=0.3, color=GOLD, spaceAfter=4),
    ])

def _section(title, ST):
    return KeepTogether([
        Spacer(1, 6),
        HRFlowable(width='100%', thickness=0.8, color=GOLD2, spaceAfter=3),
        Paragraph(title.upper(), ST['section']),
    ])

def _table(headers, rows, col_widths, ST, planet_col=None, highlight_rows=None):
    data = [[Paragraph(h, ST['table_hdr']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), ST['table_cell']) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    ts = TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  HEAD_BG),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [ROW_ODD, ROW_EVEN]),
        ('GRID',          (0,0), (-1,-1), 0.35, BORDER),
        ('LINEBELOW',     (0,0), (-1,0),  1.2, GOLD2),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 5),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ])
    if planet_col is not None:
        for i, row in enumerate(rows, 1):
            pname = str(row[planet_col]).replace('(R)','').strip()
            ts.add('TEXTCOLOR', (planet_col,i), (planet_col,i), PCOLS.get(pname, INK2))
            ts.add('FONTNAME',  (planet_col,i), (planet_col,i), 'Helvetica-Bold')
    if highlight_rows:
        for i in highlight_rows:
            ts.add('BACKGROUND', (0,i), (-1,i), GOLD_LITE)
            ts.add('FONTNAME',   (0,i), (-1,i), 'Helvetica-Bold')
            ts.add('TEXTCOLOR',  (0,i), (-1,i), INK)
    t.setStyle(ts)
    return t


# ── Main ──────────────────────────────────────────────────────────────────────
def build_pdf(kundali: dict, dasha_periods: list, current_dasha: dict,
              yogas: list, transits: list, moon_transit: dict,
              predictions: dict = None) -> bytes:

    buf  = io.BytesIO()
    ST   = _styles()
    name = kundali['name']
    dob_str  = kundali.get('dob','').replace('T',' ')[:16]
    tz_str   = kundali.get('tz','')
    dob_full = f"{dob_str}  |  {tz_str}"

    def on_page(c, doc): _page_bg(c, doc, name, dob_full)

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT+5*mm, bottomMargin=MB+5*mm,
        title=f"Vedic Horoscope - {name}",
        author="Jyotish Local Engine",
    )
    story = []
    cw = doc.width

    # ══════════════════════════════════════════
    # PAGE 1  Cover + Chart + Planet Table
    # ══════════════════════════════════════════
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width='100%', thickness=2, color=GOLD2, spaceAfter=2))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=10))
    story.append(Paragraph(name.upper(), ST['cover_name']))
    story.append(Paragraph('Vedic Horoscope  |  Jyotish Report', ST['cover_sub']))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD,
                             spaceBefore=8, spaceAfter=2))
    story.append(HRFlowable(width='100%', thickness=2, color=GOLD2, spaceAfter=10))

    # Bio strip
    lagna_lord = kundali.get('sign_lords',{}).get(kundali['lagna']['sign'],'')
    bio_items = [
        ('Date of Birth', dob_str),
        ('Timezone', tz_str),
        ('Lagna', f"{kundali['lagna']['sign']}  {kundali['lagna']['deg']}"),
        ('Lagna Lord', lagna_lord),
        ('Moon Rashi', kundali['moon_sign']),
        ('Sun Rashi', kundali['sun_sign']),
    ]
    bio_data = [[Paragraph(f"<b>{k}</b><br/>{v}", ST['body_small']) for k,v in bio_items]]
    bio_t = Table(bio_data, colWidths=[cw/6]*6)
    bio_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), CREAM2),
        ('BOX',           (0,0), (-1,-1), 1.0, GOLD2),
        ('INNERGRID',     (0,0), (-1,-1), 0.3, BORDER),
        ('LEFTPADDING',   (0,0), (-1,-1), 7),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(bio_t)
    story.append(Spacer(1, 10))

    # Chart + side panel
    chart_sz = 188

    class ChartWrapper(Flowable):
        def __init__(self, k, sz):
            super().__init__()
            self.k=k; self.sz=sz
            self.width=sz; self.height=sz
        def draw(self):
            ch = SIChart(self.k, self.sz)
            ch.canv = self.canv
            ch.draw()

    # Side info
    side_items = [
        ['Lagna', f"{kundali['lagna']['sign']} {kundali['lagna']['deg']}"],
        ['Lagna Nakshatra', kundali['lagna']['nakshatra']],
        ['Moon Nakshatra', kundali['moon_nakshatra']],
    ]
    if current_dasha:
        side_items += [
            ['', ''],
            ['Maha Dasha', current_dasha.get('maha','')],
            ['Ends', current_dasha.get('maha_end','')],
            ['Antardasha', current_dasha.get('antara','')],
            ['Ends', current_dasha.get('antara_end','')],
        ]
    # Add active yogas
    active_yogas = [y for y in yogas if y['present'] and 'Benefic' in y.get('severity','')]
    if active_yogas:
        side_items.append(['',''])
        side_items.append(['Active Yogas',''])
        for y in active_yogas[:4]:
            side_items.append(['-', y['name'].split('(')[0].strip()])

    side_data = [[
        Paragraph(f"<b>{k}</b>" if k else '', ST['body_small']),
        Paragraph(clean(v), ST['body_small'])
    ] for k,v in side_items]
    side_t = Table(side_data, colWidths=[58, 70])
    side_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), CREAM2),
        ('BOX',           (0,0), (-1,-1), 0.8, GOLD2),
        ('INNERGRID',     (0,0), (-1,-1), 0.2, BORDER2),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('TOPPADDING',    (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [CREAM, CREAM2]),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))

    gap = 8
    layout = Table(
        [[ChartWrapper(kundali, chart_sz), side_t]],
        colWidths=[chart_sz+gap, cw-chart_sz-gap]
    )
    layout.setStyle(TableStyle([
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
    ]))
    story.append(layout)
    story.append(Spacer(1, 8))

    # Planet table
    story.append(_section('Planetary Positions', ST))
    p_rows = []
    for pname, pd in kundali['planets'].items():
        p_rows.append([
            pname + ('(R)' if pd.get('retrograde') else ''),
            pd['sign'],
            f"{pd['deg']}",
            f"H{pd['house']}  {HOUSE_NAMES[pd['house']]}",
            pd['nakshatra'],
            f"Pada {pd['pada']}",
        ])
    story.append(_table(
        ['Planet','Sign','Deg','House','Nakshatra','Pada'],
        p_rows, [52,70,34,96,94,36], ST, planet_col=0
    ))

    # ══════════════════════════════════════════
    # PAGE 2  Dasha
    # ══════════════════════════════════════════
    story.append(PageBreak())
    story.append(_section('Vimshottari Dasha Timeline', ST))

    if current_dasha:
        story.append(Paragraph(
            f"<b>Active:</b>  Maha Dasha <b>{current_dasha.get('maha','')}</b> "
            f"(ends {current_dasha.get('maha_end','')})  |  "
            f"Antardasha <b>{current_dasha.get('antara','')}</b> "
            f"(ends {current_dasha.get('antara_end','')})",
            ST['body']
        ))
        story.append(Spacer(1, 6))

    d_rows   = []
    hi_rows  = []
    for idx, p in enumerate(dasha_periods[:20], 1):
        is_cur = (p['maha_lord'] == current_dasha.get('maha',''))
        if is_cur: hi_rows.append(idx)
        d_rows.append([
            p['maha_lord'] + ('  [ACTIVE]' if is_cur else ''),
            p['start'], p['end'], f"{p['years']} yrs",
        ])
    story.append(_table(
        ['Maha Dasha Lord','Start','End','Duration'],
        d_rows, [130,88,88,56], ST, highlight_rows=hi_rows
    ))
    story.append(Spacer(1, 10))

    # Current Antardasha breakdown
    for p in dasha_periods:
        if p['maha_lord'] == current_dasha.get('maha',''):
            story.append(_section(f"Antardasha — {p['maha_lord']} Maha Dasha", ST))
            ad_rows = []
            ad_hi   = []
            for j, ad in enumerate(p['antardashas'], 1):
                is_a = (ad['lord'] == current_dasha.get('antara',''))
                if is_a: ad_hi.append(j)
                ad_rows.append([
                    ad['lord'] + ('  [ACTIVE]' if is_a else ''),
                    ad['start'], ad['end'],
                ])
            story.append(_table(
                ['Antardasha Lord','Start','End'],
                ad_rows, [150,110,110], ST, highlight_rows=ad_hi
            ))
            break

    # ══════════════════════════════════════════
    # PAGE 3  Yogas + Transits
    # ══════════════════════════════════════════
    story.append(PageBreak())
    story.append(_section('Yogas & Doshas', ST))

    y_rows = []
    y_hi   = []
    for idx, y in enumerate(yogas, 1):
        if y['present']: y_hi.append(idx)
        y_rows.append([
            y['name'],
            'Active' if y['present'] else 'Absent',
            y['severity'] if y['present'] else '-',
            clean(y['description'])[:90] + ('...' if len(y['description'])>90 else ''),
        ])
    y_t = _table(['Name','Status','Severity','Description'],
                 y_rows, [120,44,52,184], ST)
    for idx, y in enumerate(yogas, 1):
        if y['present']:
            sev = y.get('severity','')
            col = TEAL if 'Benefic' in sev else (RED if sev in ['High','Medium'] else GOLD)
            y_t.setStyle(TableStyle([
                ('TEXTCOLOR', (1,idx),(2,idx), col),
                ('FONTNAME',  (1,idx),(2,idx), 'Helvetica-Bold'),
            ]))
    story.append(y_t)

    story.append(Spacer(1, 10))
    story.append(_section('Moon Transit (Gochar)', ST))
    mt = moon_transit
    story.append(Paragraph(
        f"Moon in <b>{mt.get('current_sign','')}</b> — "
        f"{mt.get('nakshatra','')} Pada {mt.get('pada','')}  |  "
        f"Effect: <b>{mt.get('effect','')}</b>",
        ST['body']
    ))
    if mt.get('description'):
        story.append(Paragraph(clean(mt['description']), ST['body_small']))
    story.append(Spacer(1, 6))

    if transits:
        tr_rows = []
        tr_t_list = []
        for p in transits[0]['planets']:
            tr_rows.append([
                p['planet']+('(R)' if p['retrograde'] else ''),
                p['sign'], f"H{p['transit_house']}", p['effect'],
            ])
        tr_t2 = _table(['Planet','Sign','Transit House','Effect'],
                        tr_rows, [72,94,90,88], ST, planet_col=0)
        for i, p in enumerate(transits[0]['planets'], 1):
            col = TEAL if p['effect']=='Favourable' else RED
            tr_t2.setStyle(TableStyle([('TEXTCOLOR',(3,i),(3,i),col)]))
        story.append(tr_t2)

    # ══════════════════════════════════════════
    # PAGE 4+  LLM Predictions
    # ══════════════════════════════════════════
    PRED_SECTIONS = [
        ('chart',   'Kundali Reading',
         'Personality, career, relationships and spiritual insights'),
        ('dasha',   'Dasha Prediction',
         'Timing and life themes indicated by current Maha and Antardasha'),
        ('transit', 'Transit Guidance',
         "Today's Gochar - auspicious activities and planetary cautions"),
        ('yoga',    'Yoga & Dosha Analysis',
         'Interpretation of active yogas and doshas with remedies'),
    ]

    predictions = predictions or {}
    has_any = any(predictions.get(k,'').strip() for k,*_ in PRED_SECTIONS)

    if has_any:
        story.append(PageBreak())
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width='100%', thickness=2, color=GOLD2, spaceAfter=2))
        story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=10))
        story.append(Paragraph('ASTROLOGICAL PREDICTIONS', ST['cover_name']))
        story.append(Paragraph(
            f"AI-assisted Jyotish interpretation for {name}", ST['cover_sub']))
        story.append(HRFlowable(width='100%', thickness=0.5, color=GOLD,
                                 spaceBefore=8, spaceAfter=2))
        story.append(HRFlowable(width='100%', thickness=2, color=GOLD2, spaceAfter=14))

        for key, heading, subtitle in PRED_SECTIONS:
            text = predictions.get(key,'').strip()
            if not text:
                continue
            story.append(_section(heading, ST))
            story.append(Paragraph(clean(subtitle), ST['body_small']))
            story.append(Spacer(1, 4))

            text = clean(text)
            for para in text.split('\n\n'):
                para = para.strip()
                if not para: continue
                if re.match(r'^(\d+\.|#{1,3}|\*\*)', para):
                    para = re.sub(r'^(\d+\.|\*+|#+)\s*','',para).replace('**','').strip()
                    if para:
                        story.append(Paragraph(para, ST['pred_h']))
                else:
                    para = para.replace('**','').replace('\n',' ')
                    if para.strip():
                        story.append(Paragraph(para, ST['pred_body']))
                story.append(Spacer(1,2))

            story.append(Spacer(1,8))
            story.append(HRFlowable(width='100%', thickness=0.4, color=BORDER, spaceAfter=4))

    # Colophon
    story.append(Spacer(1,14))
    story.append(HRFlowable(width='100%', thickness=1.0, color=GOLD2, spaceAfter=5))
    story.append(Paragraph(
        clean(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}  |  "
              f"Lahiri (Chitrapaksha) Ayanamsa  |  Placidus House System  |  "
              f"Swiss Ephemeris"),
        ST['footer']
    ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf.read()
