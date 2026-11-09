"""Rebuild the Acolhe PDF from its editable Markdown source.
Dependencies isolated in docs/.deps: reportlab, pymupdf.
This script does not publish, contact services, or edit the original logo.
"""
from pathlib import Path
import sys, re, html
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.deps'))
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Image, Table, TableStyle, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
pdfmetrics.registerFont(TTFont('Arial',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold',r'C:\Windows\Fonts\arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold',italic='Arial',boldItalic='ArialBold')
W,H=A4
TEAL=HexColor('#168C86');PEACH=HexColor('#F2A97A')
styles={
 'body':ParagraphStyle('body',fontName='Arial',fontSize=10.3,leading=14.5,spaceAfter=6,textColor=HexColor('#243434'),splitLongWords=True),
 'h1':ParagraphStyle('h1',fontName='ArialBold',fontSize=17,leading=22,spaceBefore=18,spaceAfter=11,keepWithNext=True,textColor=black),
 'h2':ParagraphStyle('h2',fontName='ArialBold',fontSize=12,leading=17,spaceBefore=12,spaceAfter=7,keepWithNext=True,textColor=black),
 'small':ParagraphStyle('small',fontName='Arial',fontSize=9,leading=13,spaceAfter=7,textColor=HexColor('#465555')),
 'bullet':ParagraphStyle('bullet',fontName='Arial',fontSize=10.3,leading=14.5,leftIndent=13,firstLineIndent=-10,spaceAfter=6,textColor=HexColor('#243434')),
 'title':ParagraphStyle('title',fontName='ArialBold',fontSize=34,leading=39,spaceAfter=14,textColor=black),
 'subtitle':ParagraphStyle('subtitle',fontName='ArialBold',fontSize=19,leading=25,spaceAfter=16,textColor=black),
 'table':ParagraphStyle('table',fontName='Arial',fontSize=9,leading=13,spaceAfter=2),
}
for style in styles.values():
 style.allowWidows=0
 style.allowOrphans=0
def inline(t):
 t=html.escape(t)
 t=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t)
 t=re.sub(r'`([^`]+)`',r'<font color="#175B57">\1</font>',t)
 return t
class Manual(BaseDocTemplate):
 def __init__(self,path):
  super().__init__(str(path),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=56,bottomMargin=52,title='Acolhe Documentação do projeto e guia de validação',author='Equipe Acolhe',pageCompression=1)
  self.addPageTemplates(PageTemplate(id='normal',frames=[Frame(52,52,W-104,H-108,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.header))
 def header(self,c,doc):
  c.saveState()
  if doc.page>1:
   c.setFillColor(TEAL);c.rect(0,H-7,W,7,fill=1,stroke=0)
   c.setFillColor(HexColor('#52615F'));c.setFont('Arial',8)
   c.drawString(52,H-33,'ACOLHE  /  DOCUMENTAÇÃO TÉCNICA')
   c.drawRightString(W-52,H-33,'FIAP 2026.2')
  c.setFont('Arial',8);c.setFillColor(HexColor('#52615F'))
  c.drawString(52,29,'Versão 0.1  |  7 de novembro de 2026')
  c.drawRightString(W-52,29,f'{doc.page}')
  c.restoreState()
 def afterFlowable(self,f):
  if isinstance(f,Paragraph) and f.style.name=='h1':
   text=f.getPlainText(); key='s'+str(self.seq.nextf('section'))
   self.canv.bookmarkPage(key)
   self.canv.addOutlineEntry(text,key,0,False)
   self.notify('TOCEntry',(0,text,self.page,key))
def parse_md(text):
 out=[]; pending=[]; rows=[]
 def flush():
  if pending:out.append(Paragraph(inline(' '.join(pending)),styles['body']));pending.clear()
 def flush_table():
  if not rows:return
  cells=[[Paragraph(inline(c),styles['table']) for c in row] for row in rows]
  n=len(cells[0]);widths=[(W-104)/n]*n
  if n==2:widths=[116,W-220]
  table=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
  table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#DCECEA')),('GRID',(0,0),(-1,-1),.4,HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
  out.extend([table,Spacer(1,12)]);rows.clear()
 for line in text.splitlines():
  line=line.strip()
  if line.startswith('|'):
   flush()
   if not re.match(r'^\|[\s|:\-]+\|$',line): rows.append([v.strip() for v in line.strip('|').split('|')])
   continue
  flush_table()
  if not line:flush();continue
  if line.startswith('# '):flush();out.append(Paragraph(inline(line[2:]),styles['h1']))
  elif line.startswith('## '):flush();out.append(Paragraph(inline(line[3:]),styles['h2']))
  elif line.startswith('- '):flush();out.append(Paragraph('• '+inline(line[2:].replace('[ ]','(  )')),styles['bullet']))
  elif re.match(r'^\d+\. ',line):flush();out.append(Paragraph(inline(line),styles['bullet']))
  else:pending.append(line)
 flush();flush_table();return out
story=[]
story.append(Spacer(1,10))
story.append(Paragraph('ACOLHE',styles['title']))
story.append(Paragraph('Documentação do projeto<br/>e guia de validação',styles['subtitle']))
story.append(Paragraph('Global Solution FIAP 2026.2 · CitizenTech',styles['body']))
logo=ROOT.parent/'app'/'static'/'logo.png'
if logo.exists():story.append(Image(str(logo),width=300,height=200,hAlign='LEFT',mask='auto'))
story.append(Spacer(1,15))
story.append(Paragraph('<b>Equipe</b>',styles['body']))
for p in ['Tomáz Versolato Carballo · RM 551417','Rony Ken Nagai · RM 551549','Aksel Viktor Caminha Rae · RM 99011','Ian Xavier Kuraoka · RM 98860']:story.append(Paragraph(p,styles['body']))
story.append(Spacer(1,14))
story.append(Paragraph('Manual para desenvolvimento, demonstração e avaliação. Reúne escopo, funcionamento, procedimentos de teste e pendências. O protótipo local não comprova a conclusão de todos os requisitos acadêmicos.',styles['small']))
story.append(PageBreak())
story.append(Paragraph('Sumário',styles['subtitle']))
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Arial',fontSize=10.5,leading=17,spaceBefore=6,leftIndent=0,firstLineIndent=0,rightIndent=20)];toc.dotsMinLevel=0
story.append(toc)
story.append(Spacer(1,20))
story.append(Paragraph('Como usar este manual',styles['h2']))
story.append(Paragraph('Comece pelos limites do MVP e pela operação local. Execute os testes da versão entregue e registre o resultado observado. Use as pendências para separar o que está preparado do que depende de modelo, infraestrutura, validação externa ou hardware real.',styles['body']))
story.append(PageBreak())
source=(ROOT/'manual_acolhe.md').read_text(encoding='utf-8-sig')
source=source[source.index('# 1 Visão geral'):]
story.extend(parse_md(source))
doc=Manual(ROOT/'manual_acolhe.pdf');doc.multiBuild(story)
import pymupdf
pdf=pymupdf.open(ROOT/'manual_acolhe.pdf');qa=ROOT/'qa';qa.mkdir(exist_ok=True)
texts=[]
for i,p in enumerate(pdf):
 p.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(qa/f'page-{i+1:02}.png')
 texts.append(p.get_text())
(qa/'pdf_texto.txt').write_text('\n\n'.join(texts),encoding='utf-8')
print(f'Generated {len(pdf)} pages: {ROOT / "manual_acolhe.pdf"}')

