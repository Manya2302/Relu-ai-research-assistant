from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics.widgets.markers import makeMarker

from app.schemas.research import CompanyKnowledgeGraph, CompanyResearchResult, ResearchSource


@dataclass(slots=True)
class SectionBlock:
    title: str
    paragraphs: list[str]
    bullets: list[str] | None = None
    table: list[list[Any]] | None = None


class PDFService:
    def __init__(self) -> None:
        self.styles = getSampleStyleSheet()
        self._build_styles()

    def build_pdf(self, result: CompanyResearchResult) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=54,
            bottomMargin=48,
            title=self._report_title(result),
            author='Relu Company Intelligence Platform',
        )

        story: list[Any] = []
        sections = self._build_sections(result)

        story.extend(self._cover_page(result))
        story.append(PageBreak())
        story.extend(self._snapshot_page(result))

        for section in sections:
            story.append(PageBreak())
            story.extend(self._section_page(section))

        story.append(PageBreak())
        story.extend(self._appendix_pages(result))

        doc.build(
            story,
            onFirstPage=self._draw_page,
            onLaterPages=self._draw_page,
        )
        return buffer.getvalue()

    def generate_pdf(self, result: CompanyResearchResult) -> bytes:
        return self.build_pdf(result)

    def filename_for(self, result: CompanyResearchResult) -> str:
        slug = self._slugify(result.company_name or 'company-intelligence-report')
        stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f'{slug}_{stamp}.pdf'

    def _build_styles(self) -> None:
        self.styles.add(
            ParagraphStyle(
                name='ReportTitle',
                parent=self.styles['Title'],
                fontName='Helvetica-Bold',
                fontSize=22,
                leading=26,
                textColor=colors.HexColor('#0F172A'),
                alignment=TA_LEFT,
                spaceAfter=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name='ReportSubtitle',
                parent=self.styles['BodyText'],
                fontName='Helvetica',
                fontSize=10.5,
                leading=14,
                textColor=colors.HexColor('#475569'),
                spaceAfter=8,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name='SectionTitle',
                parent=self.styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=16,
                leading=20,
                textColor=colors.HexColor('#0F172A'),
                spaceAfter=10,
                spaceBefore=6,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name='MinorTitle',
                parent=self.styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=12,
                leading=15,
                textColor=colors.HexColor('#1E293B'),
                spaceAfter=6,
                spaceBefore=6,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name='SmallBody',
                parent=self.styles['BodyText'],
                fontName='Helvetica',
                fontSize=9,
                leading=12,
                textColor=colors.HexColor('#334155'),
            )
        )
        self.styles.add(
            ParagraphStyle(
                name='MetricValue',
                parent=self.styles['BodyText'],
                fontName='Helvetica-Bold',
                fontSize=11,
                leading=13,
                textColor=colors.HexColor('#0F172A'),
            )
        )
        self.styles.add(
            ParagraphStyle(
                name='MetricLabel',
                parent=self.styles['BodyText'],
                fontName='Helvetica',
                fontSize=8,
                leading=10,
                textColor=colors.HexColor('#64748B'),
            )
        )

    def _cover_page(self, result: CompanyResearchResult) -> list[Any]:
        company_name = self._text(result.company_name, 'Unknown Company')
        timestamp = result.generated_at.strftime('%d %b %Y') if result.generated_at else datetime.utcnow().strftime('%d %b %Y')
        story: list[Any] = []
        story.append(Spacer(1, 0.6 * inch))
        story.append(Paragraph('Company Intelligence Report', self.styles['ReportSubtitle']))
        story.append(Paragraph(company_name, self.styles['ReportTitle']))
        story.append(Paragraph(self._cover_summary(result), self.styles['BodyText']))
        story.append(Spacer(1, 0.25 * inch))

        story.append(self._summary_card_grid(result))
        story.append(Spacer(1, 0.18 * inch))
        story.append(self._create_overview_chart(result))
        story.append(Spacer(1, 0.18 * inch))
        story.append(Paragraph(f'Report generated on {timestamp}', self.styles['SmallBody']))
        story.append(Paragraph('Prepared from structured crawl data, public web discovery, and AI analysis.', self.styles['SmallBody']))
        return story

    def _snapshot_page(self, result: CompanyResearchResult) -> list[Any]:
        story: list[Any] = [Paragraph('Snapshot', self.styles['SectionTitle'])]
        story.append(Paragraph(self._snapshot_intro(result), self.styles['BodyText']))
        story.append(Spacer(1, 0.16 * inch))
        story.append(self._build_snapshot_table(result))
        story.append(Spacer(1, 0.18 * inch))
        story.append(self._build_source_mix_chart(result))
        return story

    def _section_page(self, section: SectionBlock) -> list[Any]:
        story: list[Any] = [Paragraph(section.title, self.styles['SectionTitle'])]
        for paragraph in section.paragraphs:
            story.append(Paragraph(paragraph, self.styles['BodyText']))
            story.append(Spacer(1, 0.08 * inch))

        if section.bullets:
            story.append(self._bullets(section.bullets))
            story.append(Spacer(1, 0.1 * inch))

        if section.table:
            if isinstance(section.table, Table):
                story.append(section.table)
            else:
                story.append(self._section_table(section.title, section.table))
            story.append(Spacer(1, 0.1 * inch))

        chart = self._section_chart(section.title)
        if chart is not None:
            story.append(chart)
        return story

    def _section_table(self, title: str, rows: list[list[Any]]) -> Table:
        normalized = title.lower()
        if normalized == 'company profile':
            return self._table(rows, [1.4 * inch, 1.9 * inch, 2.9 * inch], header=True)
        if normalized == 'financial analysis':
            return self._table(rows, [1.9 * inch, 1.4 * inch, 2.9 * inch], header=True)
        if normalized == 'competitor analysis':
            return self._table(rows, [1.8 * inch, 1.0 * inch, 3.4 * inch], header=True)
        if normalized == 'global presence':
            return self._table(rows, [1.8 * inch, 0.9 * inch, 3.5 * inch], header=True)
        if normalized == 'news and market activity':
            return self._table(rows, [2.0 * inch, 0.9 * inch, 3.3 * inch], header=True)
        if normalized == 'risk analysis':
            return self._table(rows, [1.8 * inch, 0.9 * inch, 3.5 * inch], header=True)
        return self._table(rows, [1.8 * inch, 1.2 * inch, 3.2 * inch], header=True)

    def _appendix_pages(self, result: CompanyResearchResult) -> list[Any]:
        story: list[Any] = [Paragraph('Appendix', self.styles['SectionTitle'])]
        story.append(Paragraph('This appendix consolidates the evidence base, crawler statistics, references, and raw signal inventory used to produce the report.', self.styles['BodyText']))
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph('Crawler Statistics', self.styles['MinorTitle']))
        if not result.crawler_pages:
            story.append(Paragraph('Note: 0 pages crawled indicates the target site blocked automated access. In these cases, the report is generated from public references and search discovery.', self.styles['SmallBody']))
            story.append(Spacer(1, 0.08 * inch))
        story.append(self._crawler_stats_table(result))
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph('References', self.styles['MinorTitle']))
        story.append(self._references_table(result.sources, result.references))
        story.append(PageBreak())
        story.append(Paragraph('Web Contact Signals', self.styles['SectionTitle']))
        story.append(Paragraph('These rows are extracted directly from crawled pages, so phone numbers, addresses, and page-level evidence remain visible even if the AI response is incomplete.', self.styles['BodyText']))
        story.append(Spacer(1, 0.12 * inch))
        story.append(self._contact_signals_table(result))
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph('Knowledge Graph', self.styles['SectionTitle']))
        story.append(self._knowledge_graph_table(result.knowledge_graph))
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph('Evidence Notes', self.styles['MinorTitle']))
        story.append(self._evidence_notes(result))
        return story

    def _build_sections(self, result: CompanyResearchResult) -> list[SectionBlock]:
        graph = result.knowledge_graph or CompanyKnowledgeGraph()
        competitors = [self._source_or_name(item) for item in (result.competitors or [])[:5]]
        sources = result.sources or []

        section_data = [
            SectionBlock(
                title='Executive Summary',
                paragraphs=[
                    self._summary_paragraph(result),
                    self._market_paragraph(result),
                    self._risk_paragraph(result),
                ],
                bullets=self._summary_bullets(result),
            ),
            SectionBlock(
                title='Company Profile',
                paragraphs=[
                    self._profile_paragraph(result, graph),
                    self._identity_paragraph(result),
                ],
                table=self._profile_table(result, graph),
            ),
            SectionBlock(
                title='Products and Services',
                paragraphs=[
                    self._products_paragraph(result, graph),
                    self._offerings_paragraph(result),
                ],
                bullets=self._product_bullets(result, graph),
                table=self._mini_table('Key Offerings', self._pair_rows(result.products or self._graph_values(graph, 'products'))),
            ),
            SectionBlock(
                title='Financial Analysis',
                paragraphs=[
                    self._financial_paragraph(result, graph),
                    self._valuation_paragraph(result),
                ],
                table=self._financial_table(result, graph),
            ),
            SectionBlock(
                title='Competitor Analysis',
                paragraphs=[
                    self._competitor_paragraph(result, competitors),
                    self._positioning_paragraph(result),
                ],
                table=self._competitor_table(result),
            ),
            SectionBlock(
                title='Leadership',
                paragraphs=[
                    self._leadership_paragraph(result, graph),
                    self._capability_paragraph(result, graph),
                ],
                bullets=self._leadership_bullets(result, graph),
            ),
            SectionBlock(
                title='Global Presence',
                paragraphs=[
                    self._global_paragraph(result, graph),
                    self._office_paragraph(result, graph),
                ],
                table=self._presence_table(result, graph),
            ),
            SectionBlock(
                title='Hiring and Talent Signals',
                paragraphs=[
                    self._hiring_paragraph(result, graph),
                    self._talent_paragraph(result),
                ],
                bullets=self._hiring_bullets(result, graph),
            ),
            SectionBlock(
                title='Technology and Digital Footprint',
                paragraphs=[
                    self._technology_paragraph(result, graph),
                    self._digital_paragraph(result),
                ],
                bullets=self._technology_bullets(result, graph),
            ),
            SectionBlock(
                title='News and Market Activity',
                paragraphs=[
                    self._news_paragraph(result, sources),
                    self._events_paragraph(result, graph),
                ],
                table=self._news_table(sources),
            ),
            SectionBlock(
                title='Risk Analysis',
                paragraphs=[
                    self._risk_analysis_paragraph(result, graph),
                    self._risk_mitigation_paragraph(result),
                ],
                bullets=self._risk_bullets(result, graph),
            ),
            SectionBlock(
                title='AI Insights',
                paragraphs=[
                    self._ai_paragraph(result),
                    self._recommendation_paragraph(result),
                ],
                bullets=self._ai_bullets(result, graph),
            ),
        ]
        return section_data

    def _summary_card_grid(self, result: CompanyResearchResult) -> Table:
        metrics = [
            ('Company', self._text(result.company_name, 'Unknown')),
            ('Industry', self._text(result.industry, 'Unclassified')),
            ('Country', self._text(result.country, 'Unknown')),
            ('Website', self._text(result.website, 'Not available')),
            ('Phone', self._text(result.phone, 'N/A')),
            ('Address', self._text(result.address, 'N/A')),
            ('Revenue', self._text(result.revenue, 'Not disclosed')),
            ('Competitors', str(len(result.competitors or []))),
            ('Sources', str(len(result.sources or []))),
            ('Signals', str(len(result.knowledge_graph.profile) + len(result.knowledge_graph.products) + len(result.knowledge_graph.services))),
        ]
        rows: list[list[Any]] = []
        for idx in range(0, len(metrics), 2):
            left = metrics[idx]
            right = metrics[idx + 1] if idx + 1 < len(metrics) else ('', '')
            rows.append([
                self._metric_box(left[0], left[1]),
                self._metric_box(right[0], right[1]) if right[0] else '',
            ])
        table = Table(rows, colWidths=[3.0 * inch, 3.0 * inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return table

    def _metric_box(self, label: str, value: str) -> Table:
        table = Table([[Paragraph(value, self.styles['MetricValue'])], [Paragraph(label, self.styles['MetricLabel'])]], colWidths=[2.9 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#E2E8F0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        return table

    def _create_overview_chart(self, result: CompanyResearchResult) -> Drawing:
        drawing = Drawing(520, 170)
        chart = VerticalBarChart()
        chart.x = 45
        chart.y = 30
        chart.height = 110
        chart.width = 430
        chart.data = [[
            len(result.sources or []),
            len(result.references or result.sources or []),
            len(result.competitors or []),
            len(result.products or []),
            len(result.pain_points or []),
        ]]
        chart.categoryAxis.categoryNames = ['Sources', 'Refs', 'Comps', 'Prod', 'Risks']
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(5, max(chart.data[0]) + 1)
        chart.valueAxis.valueStep = max(1, int(chart.valueAxis.valueMax / 5))
        chart.bars[0].fillColor = colors.HexColor('#2563EB')
        chart.barWidth = 16
        chart.strokeColor = colors.HexColor('#CBD5E1')
        drawing.add(chart)
        drawing.add(String(10, 150, 'Evidence Coverage Overview', fontName='Helvetica-Bold', fontSize=10, fillColor=colors.HexColor('#0F172A')))
        return drawing

    def _build_snapshot_table(self, result: CompanyResearchResult) -> Table:
        rows = [
            ['Core Signal', 'Value', 'Interpretation'],
            ['Company profile', self._text(result.company_name, 'Unknown'), self._snapshot_text(result.company_name, 'entity identified from structured extraction')],
            ['Industry', self._text(result.industry, 'Unclassified'), self._snapshot_text(result.industry, 'industry inferred from public sources')],
            ['Country', self._text(result.country, 'Unknown'), self._snapshot_text(result.country, 'geographic footprint')],
            ['Products', str(len(result.products or [])), self._snapshot_text(result.products, 'offerings extracted from the company footprint')],
            ['Competitors', str(len(result.competitors or [])), self._snapshot_text(result.competitors, 'competitive set observed in research')],
        ]
        return self._table(rows, [1.7 * inch, 0.9 * inch, 3.4 * inch], header=True)

    def _build_source_mix_chart(self, result: CompanyResearchResult) -> Drawing:
        drawing = Drawing(520, 210)
        chart = Pie()
        chart.x = 50
        chart.y = 20
        chart.width = 170
        chart.height = 170
        chart.data = [
            max(1, len(result.sources or [])),
            max(1, len(result.references or [])),
            max(1, len(result.crawler_pages or [])),
        ]
        chart.labels = ['Public sources', 'References', 'Crawled pages']
        chart.slices.strokeWidth = 0.6
        chart.slices[0].fillColor = colors.HexColor('#2563EB')
        chart.slices[1].fillColor = colors.HexColor('#0F766E')
        chart.slices[2].fillColor = colors.HexColor('#F59E0B')
        legend = Legend()
        legend.x = 250
        legend.y = 125
        legend.dx = 8
        legend.dy = 8
        legend.fontName = 'Helvetica'
        legend.fontSize = 8
        legend.alignment = 'right'
        legend.boxAnchor = 'nw'
        legend.columnMaximum = 3
        legend.colorNamePairs = [
            (colors.HexColor('#2563EB'), 'Public sources'),
            (colors.HexColor('#0F766E'), 'References'),
            (colors.HexColor('#F59E0B'), 'Crawled pages'),
        ]
        drawing.add(chart)
        drawing.add(legend)
        drawing.add(String(245, 190, 'Source Mix', fontName='Helvetica-Bold', fontSize=10, fillColor=colors.HexColor('#0F172A')))
        return drawing

    def _table(self, rows: list[list[Any]], col_widths: list[float], header: bool = False) -> Table:
        table = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5),
            ('LEADING', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]
        if not header:
            style.extend([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ])
        table.setStyle(TableStyle(style))
        return table

    def _mini_table(self, heading: str, rows: list[list[str]]) -> Table:
        body = [[Paragraph(heading, self.styles['MinorTitle'])], [self._table([['Item', 'Details'], *rows], [1.8 * inch, 4.4 * inch], header=True)]]
        table = Table(body, colWidths=[6.2 * inch])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#CBD5E1')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFFFFF')),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return table

    def _summary_paragraph(self, result: CompanyResearchResult) -> str:
        company = self._text(result.company_name, 'The company')
        industry = self._text(result.industry, 'the target market')
        country = self._text(result.country, 'the operating geography')
        products = self._count_text(result.products, 'offerings')
        competitors = self._count_text(result.competitors, 'competitors')
        return f'{company} appears positioned within {industry} and is operating across {country}. The evidence set indicates {products}, while the benchmark set includes {competitors}. The report combines crawling, public-source discovery, and structured AI analysis to produce a board-ready view of the business.'

    def _market_paragraph(self, result: CompanyResearchResult) -> str:
        return f'The platform treats the company as a dynamic intelligence target rather than a fixed-profile entity. That means the findings are synthesized from the official site, public signals, and research references, then translated into an operating picture that can support business development, procurement, and strategy reviews.'

    def _risk_paragraph(self, result: CompanyResearchResult) -> str:
        pain_points = self._count_text(result.pain_points, 'risk themes')
        return f'The current risk picture is shaped by {pain_points}, along with gaps in public disclosure. Where direct disclosures are limited, the report marks the area as an inference and surfaces it in the appendix rather than overstating certainty.'

    def _summary_bullets(self, result: CompanyResearchResult) -> list[str]:
        return [
            f'Primary website: {self._text(result.website, "not available")}',
            f'Public source footprint: {len(result.sources or [])} sources with deduplicated references',
            f'Competitor set captured: {len(result.competitors or [])} organizations',
            f'AI output is structured from JSON and knowledge-graph evidence, not raw HTML',
        ]

    def _profile_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        profile_count = len(graph.profile or [])
        return f'The structured graph contains {profile_count} profile signals, which are used to normalize the company name, brand descriptors, and context across sources. This section anchors the report with the entity identity that the remaining sections build upon.'

    def _identity_paragraph(self, result: CompanyResearchResult) -> str:
        return f'Known identifiers in the result set include the corporate website, country, and industry classification. If a field is missing, the report preserves the gap rather than filling it with speculative content, which keeps the intelligence layer usable for downstream review.'

    def _profile_table(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[list[Any]]:
        source_note = 'Extracted from public discovery/AI' if not result.crawler_pages else 'Extracted from crawl or AI'
        return [
            ['Attribute', 'Value', 'Notes'],
            ['Company', self._text(result.company_name, 'Unknown'), 'Primary company label'],
            ['Website', self._text(result.website, 'Not available'), 'Official domain or dominant property'],
            ['Phone', self._text(result.phone, 'N/A'), source_note],
            ['Address', self._text(result.address, 'N/A'), source_note],
            ['Industry', self._text(result.industry, 'Unclassified'), 'Detected from the evidence set'],
            ['Country', self._text(result.country, 'Unknown'), 'Primary geography'],
            ['Leadership signals', str(len(graph.leadership or [])), 'Named leadership references'],
            ['Offices', str(len(graph.offices or [])), 'Presence nodes and office locations'],
        ]

    def _products_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        return f'Product and service intelligence is assembled from the knowledge graph as well as any named products in the AI response. The graph currently holds {len(graph.products or [])} product signals and {len(graph.services or [])} service signals, which is enough to generate a usable operating inventory even when the site is fragmented or partially blocked.'

    def _offerings_paragraph(self, result: CompanyResearchResult) -> str:
        return 'The report emphasizes the offerings that are most visible from public web evidence, then separates explicit listings from inferred lines of business. That distinction is important when the target has a broad catalog, a partner ecosystem, or multiple business units.'

    def _product_bullets(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[str]:
        product_values = result.products or graph.products or []
        if not product_values:
            return ['No explicit product names were extracted; use the references section to inspect evidence sources.']
        return [self._to_sentence(item) for item in product_values[:6]]

    def _financial_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        return f'Financial analysis uses revenue, valuation, market-cap, and funding signals when they are available, while gracefully degrading to “not disclosed” if the public footprint is incomplete. The knowledge graph contributes {len(graph.financials or [])} financial signal groups, giving the report enough structure to present a board-level view without inventing hard numbers.'

    def _valuation_paragraph(self, result: CompanyResearchResult) -> str:
        revenue = self._text(result.revenue, 'not disclosed')
        return f'Current revenue signal: {revenue}. Where the company is private or does not publish financials, the report can still present a qualitative view of scale, momentum, and disclosure quality rather than leaving the page blank.'

    def _financial_table(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[list[Any]]:
        return [
            ['Metric', 'Signal', 'Interpretation'],
            ['Revenue', self._text(result.revenue, 'Not disclosed'), 'Top-line visibility'],
            ['Market Cap', self._text(getattr(result, 'market_cap', ''), self._financial_signal(graph, 'market_cap')), 'Visible for public issuers'],
            ['Funding/Valuation', self._text(getattr(result, 'funding', ''), self._financial_signal(graph, 'funding')), 'Used when the company is private or venture-backed'],
            ['Financial signals', str(len(graph.financials or [])), 'Extracted finance-related nodes'],
            ['Investor activity', self._financial_signal(graph, 'investors'), 'Signals from the evidence graph'],
        ]

    def _competitor_paragraph(self, result: CompanyResearchResult, competitors: list[str]) -> str:
        count = len(competitors)
        if count == 0:
            return 'No reliable competitor set was extracted, so the platform keeps this section qualitative and pushes the evidence trail into the appendix.'
        return f'The competitive set contains {count} directly identified rivals or adjacent players. The report prioritizes comparable organizations that are visible in public discovery and then labels each competitor by source confidence.'

    def _positioning_paragraph(self, result: CompanyResearchResult) -> str:
        return 'Positioning is interpreted from product breadth, location footprint, hiring intensity, and technology signals. This gives a more resilient view than relying on a single keyword match or a single search result.'

    def _competitor_table(self, result: CompanyResearchResult) -> list[list[Any]]:
        rows = [['Competitor', 'Similarity', 'Notes']]
        competitors = result.competitors or []
        if not competitors:
            rows.append(['No explicit competitors found', 'Low', 'Research set did not expose a direct peer list'])
            return rows
        for competitor in competitors[:5]:
            name = getattr(competitor, 'name', self._text(str(competitor), ''))
            reason = getattr(competitor, 'reason', '')
            rows.append([name or 'Unknown', getattr(competitor, 'similarity', 'Medium'), reason or 'Public signal'])
        return rows

    def _leadership_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        leaders = len(graph.leadership or [])
        return f'Leadership signals are taken from the graph rather than trying to hallucinate an org chart. The current evidence set includes {leaders} named leadership references, which is enough to identify whether the company presents a conventional executive layer or a sparse public profile.'

    def _capability_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        customers = len(graph.customers or [])
        partners = len(graph.partners or [])
        investors = len(graph.investors or [])
        return f'Adjacent ecosystem signals include {customers} customer references, {partners} partner references, and {investors} investor references. Those relationships often matter more than a simple management list when the report is used for commercial diligence.'

    def _leadership_bullets(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[str]:
        if not result.leadership_info:
            return ['No explicit leadership names were extracted from the current evidence set.']
        
        info = result.leadership_info
        bullets = []
        if info.ceo: bullets.append(f"CEO: {info.ceo}")
        if info.cfo: bullets.append(f"CFO: {info.cfo}")
        if info.cto: bullets.append(f"CTO: {info.cto}")
        for founder in info.founders:
            bullets.append(f"Founder: {founder}")
        for board_member in info.board_members:
            bullets.append(f"Board Member: {board_member}")
            
        if not bullets:
            return ['No explicit leadership names were extracted from the current evidence set.']
            
        return [self._to_sentence(item) for item in bullets[:6]]

    def _global_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        offices = len(graph.offices or [])
        locations = len(graph.locations or [])
        return f'Global presence is estimated from office and location signals. The knowledge graph currently holds {offices} office nodes and {locations} location nodes, which helps separate operational footprint from simple mailing-address mentions.'

    def _office_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        return 'If the company publishes regional entities, warehouses, support centers, or sales offices, those appear here. When disclosure is weak, the section can still show where the company is visibly active, which is often enough for market entry planning.'

    def _presence_table(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[list[Any]]:
        return [
            ['Presence Type', 'Count', 'Interpretation'],
            ['Offices', str(len(graph.offices or [])), 'Physical locations in the graph'],
            ['Locations', str(len(graph.locations or [])), 'General geographies and addresses'],
            ['Countries', self._text(result.country, 'Unknown'), 'Primary country signal'],
            ['Social channels', str(len(graph.social_media or [])), 'Distribution and engagement footprint'],
        ]

    def _hiring_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        careers = len(graph.careers or [])
        employees = len(graph.employees or [])
        return f'Hiring is treated as a strategic indicator rather than an HR vanity metric. The graph currently captures {careers} career signals and {employees} employee references, which can reveal expansion, capability gaps, or reorganization patterns.'

    def _talent_paragraph(self, result: CompanyResearchResult) -> str:
        return 'A company that publishes active hiring pages, role families, or engineering jobs usually leaves strong market signals even when financials are sparse. This section highlights that evidence and translates it into a growth interpretation.'

    def _hiring_bullets(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[str]:
        values = graph.careers or []
        if not values:
            return ['No direct careers or job signals were extracted.']
        return [self._to_sentence(item) for item in values[:6]]

    def _technology_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        tech_count = len(graph.technology or [])
        return f'Technology analysis groups product stack clues, engineering references, platform mentions, and developer-facing signals. The current graph contains {tech_count} technology references, which can still surface architecture patterns even when the official site is partially blocked.'

    def _digital_paragraph(self, result: CompanyResearchResult) -> str:
        return 'The digital footprint also includes docs, blogs, APIs, GitHub references, and social channels. Those properties are useful for distinguishing a mature platform business from a traditional services company.'

    def _technology_bullets(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[str]:
        values = graph.technology or []
        if not values:
            return ['No detailed technology stack signals were available.']
        return [self._to_sentence(item) for item in values[:6]]

    def _news_paragraph(self, result: CompanyResearchResult, sources: list[ResearchSource]) -> str:
        return f'News and market activity are drawn from public discovery sources, which typically include press, blog, investor, and product pages. The current source inventory contains {len(sources)} items, giving the report enough context to distinguish durable news flow from one-off mentions.'

    def _events_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        events = len(graph.events or [])
        blogs = len(graph.blogs or [])
        return f'The graph currently holds {events} event references and {blogs} blog references. That combination helps show whether the company is actively communicating roadmap, partnerships, launches, or market expansion.'

    def _news_table(self, sources: list[ResearchSource]) -> list[list[Any]]:
        rows = [['Source', 'Type', 'Notes']]
        
        # Sort sources by type for better organization
        classified = [(source, self._classify_source(source.url)) for source in sources[:12]]
        order_map = {'Official': 1, 'News': 2, 'Careers': 3, 'Market Research': 4, 'Reference': 5, 'Social Media': 6, 'Public Web': 7}
        classified.sort(key=lambda x: order_map.get(x[1], 10))
        
        for source, type_ in classified:
            rows.append([source.title or source.url, type_, self._text(source.snippet, 'Public source')])
            
        if len(rows) == 1:
            rows.append(['No news sources identified', 'N/A', 'Public discovery did not surface a dedicated feed'])
        return rows

    def _risk_analysis_paragraph(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> str:
        risks = len(result.pain_points or []) + len(graph.research or [])
        return f'Risk analysis aggregates the explicit pain points returned by the AI model and the softer uncertainty signals from the knowledge graph. The current report surfaces {risks} risk-adjacent items, which is usually enough to form an actionable diligence view.'

    def _risk_mitigation_paragraph(self, result: CompanyResearchResult) -> str:
        return 'Typical mitigations include source triangulation, additional manual review, and a targeted follow-up crawl on any sections where disclosure was sparse or contradictory. The appendix preserves those gaps so the user can make that follow-up efficiently.'

    def _risk_bullets(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[str]:
        bullets = list(result.pain_points or [])
        if not bullets:
            bullets = ['Disclosure gaps', 'Source inconsistency', 'Blocked crawling on the official site']
        return [self._to_sentence(item) for item in bullets[:6]]

    def _ai_paragraph(self, result: CompanyResearchResult) -> str:
        return 'The AI layer is intentionally asked to reason over structured evidence rather than raw markup. That keeps the output more stable, reduces prompt size, and makes the final report easier to audit.'

    def _recommendation_paragraph(self, result: CompanyResearchResult) -> str:
        return 'Recommended next steps depend on the use case: sales teams should focus on product fit, analysts should inspect the financial and risk pages, and operators should review the hiring, tech, and presence sections for growth signals.'

    def _ai_bullets(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[str]:
        bullets = list(result.recommendations or [])
        if not bullets:
            bullets = [
                'Use the appendix to validate each claim against its evidence source.',
                'Treat missing values as signal, not noise: sparse disclosure often matters.',
                'Re-run the report after a crawl refresh if the target publishes news or product updates frequently.',
            ]
        return [self._to_sentence(item) for item in bullets[:5]]

    def _knowledge_graph_table(self, graph: CompanyKnowledgeGraph) -> Table:
        rows = [['Node Group', 'Count', 'Examples']]
        groups = [
            ('profile', graph.profile),
            ('leadership', graph.leadership),
            ('financials', graph.financials),
            ('products', graph.products),
            ('services', graph.services),
            ('locations', graph.locations),
            ('offices', graph.offices),
            ('careers', graph.careers),
            ('technology', graph.technology),
            ('news', graph.news),
            ('events', graph.events),
            ('blogs', graph.blogs),
            ('customers', graph.customers),
            ('partners', graph.partners),
            ('investors', graph.investors),
            ('social media', graph.social_media),
            ('competitors', graph.competitors),
            ('research', graph.research),
        ]
        for label, values in groups:
            rows.append([label, str(len(values or [])), ', '.join(self._compact_values(values)) or 'None'])
        return self._table(rows, [1.6 * inch, 0.8 * inch, 3.8 * inch], header=True)

    def _evidence_notes(self, result: CompanyResearchResult) -> Table:
        rows = [['Evidence Type', 'Count', 'Commentary']]
        rows.append(['Public sources', str(len(result.sources or [])), 'Search and discovery inputs'])
        rows.append(['References', str(len(result.references or [])), 'Deduplicated source list for the appendix'])
        rows.append(['Crawled pages', str(len(result.crawler_pages or [])), 'Internal crawl artifacts captured by the backend'])
        rows.append(['Crawl stats keys', str(len(result.crawler_stats or {})), 'Operational metadata for debugging and auditability'])
        rows.append(['Competitors', str(len(result.competitors or [])), 'Competitive intelligence nodes'])
        return self._table(rows, [1.4 * inch, 0.9 * inch, 3.9 * inch], header=True)

    def _contact_signals_table(self, result: CompanyResearchResult) -> Table:
        rows = [['Page', 'Phones', 'Addresses', 'Notes']]
        pages = result.crawler_pages or []
        for page in pages[:12]:
            phones = ', '.join(page.phone_numbers[:3]) if page.phone_numbers else 'None'
            addresses = ', '.join(page.addresses[:3]) if page.addresses else 'None'
            notes = page.title or self._shorten(page.text or '', 70)
            rows.append([
                self._shorten(page.url, 34),
                self._shorten(phones, 30),
                self._shorten(addresses, 30),
                self._shorten(notes, 60),
            ])
        if len(rows) == 1:
            rows.append(['No crawled pages', 'None', 'None', 'Crawler returned no extractable page records'])
        return self._table(rows, [1.7 * inch, 1.2 * inch, 1.3 * inch, 2.0 * inch], header=True)

    def _crawler_stats_table(self, result: CompanyResearchResult) -> Table:
        stats = result.crawler_stats or {}
        rows = [['Metric', 'Value', 'Meaning']]
        for key in ['pages_crawled', 'total_urls', 'internal_links', 'external_links', 'documents', 'images', 'videos', 'sources_used', 'extraction_time_seconds', 'ai_tokens_estimate']:
            value = stats.get(key, 0)
            rows.append([key.replace('_', ' ').title(), str(value), self._stat_meaning(key)])
        return self._table(rows, [1.7 * inch, 0.9 * inch, 3.4 * inch], header=True)

    def _references_table(self, sources: list[ResearchSource], references: list[ResearchSource]) -> Table:
        combined = list(references or sources or [])
        rows = [['Reference', 'URL', 'Snippet']]
        for source in combined[:14]:
            rows.append([
                source.title or 'Reference',
                self._shorten(source.url, 45),
                self._shorten(source.snippet or 'Source used for evidence', 80),
            ])
        if len(rows) == 1:
            rows.append(['No references available', 'N/A', 'The source set was empty'])
        return self._table(rows, [1.6 * inch, 2.1 * inch, 2.4 * inch], header=True)

    def _section_chart(self, title: str) -> Drawing | None:
        # User requested factual business metrics, so we are removing heuristic charts
        return None

    def _horizontal_signals_chart(self, title: str, values: list[int], labels: list[str]) -> Drawing:
        drawing = Drawing(520, 180)
        chart = HorizontalBarChart()
        chart.x = 120
        chart.y = 20
        chart.height = 120
        chart.width = 360
        chart.data = [values]
        chart.categoryAxis.categoryNames = labels
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(values) + 1
        chart.valueAxis.valueStep = 1
        chart.bars[0].fillColor = colors.HexColor('#2563EB')
        chart.barWidth = 12
        drawing.add(chart)
        drawing.add(String(12, 150, title, fontName='Helvetica-Bold', fontSize=10, fillColor=colors.HexColor('#0F172A')))
        return drawing

    def _risk_chart(self) -> Drawing:
        drawing = Drawing(520, 180)
        chart = HorizontalLineChart()
        chart.x = 60
        chart.y = 30
        chart.height = 120
        chart.width = 400
        chart.data = [[2, 3, 5, 4, 6]]
        chart.categoryAxis.categoryNames = ['Disclosure', 'Coverage', 'Consistency', 'Freshness', 'Confidence']
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = 7
        chart.valueAxis.valueStep = 1
        chart.lines[0].strokeColor = colors.HexColor('#DC2626')
        chart.lines[0].symbol = makeMarker('Circle')
        drawing.add(chart)
        drawing.add(String(12, 150, 'Risk Pattern (AI Confidence Score 0-10)', fontName='Helvetica-Bold', fontSize=10, fillColor=colors.HexColor('#0F172A')))
        return drawing

    def _draw_page(self, canvas, doc) -> None:
        canvas.saveState()
        width, height = letter
        canvas.setFillColor(colors.HexColor('#0F172A'))
        canvas.rect(0, height - 36, width, 36, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawString(36, height - 24, 'Relu Company Intelligence Platform')
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(width - 36, height - 24, f'Page {canvas.getPageNumber()}')
        canvas.setStrokeColor(colors.HexColor('#CBD5E1'))
        canvas.setLineWidth(0.5)
        canvas.line(36, 42, width - 36, 42)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.setFont('Helvetica', 7)
        canvas.drawString(36, 28, 'Structured report generated from crawled evidence, public discovery, and AI synthesis.')
        canvas.restoreState()

    def _report_title(self, result: CompanyResearchResult) -> str:
        return f'{self._text(result.company_name, "Company")} Intelligence Report'

    def _cover_summary(self, result: CompanyResearchResult) -> str:
        return f'This report compiles an executive-grade intelligence view of {self._text(result.company_name, "the target company")}, combining website extraction, public web discovery, structured knowledge-graph analysis, competitor signals, and AI-generated synthesis into a single board-ready document.'

    def _snapshot_intro(self, result: CompanyResearchResult) -> str:
        return 'The snapshot condenses the strongest signals collected during discovery so the reader can quickly understand the breadth of the evidence set before moving into the detailed sections.'

    def _source_or_name(self, value: Any) -> str:
        if isinstance(value, ResearchSource):
            return value.title or value.url
        return self._text(getattr(value, 'name', '') or str(value), 'Unknown')

    def _pair_rows(self, values: list[str]) -> list[list[str]]:
        if not values:
            return [['No data', 'No data available']]
        rows: list[list[str]] = []
        for idx in range(0, len(values), 2):
            left = values[idx]
            right = values[idx + 1] if idx + 1 < len(values) else ''
            rows.append([self._shorten(self._to_sentence(left), 30), self._shorten(self._to_sentence(right), 60) if right else ''])
        return rows

    def _bullets(self, bullets: list[str]) -> Table:
        items = [[Paragraph(f'• {self._text(item)}', self.styles['BodyText'])] for item in bullets]
        table = Table(items, colWidths=[6.2 * inch])
        table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return table

    def _text(self, value: Any, fallback: str = '') -> str:
        if value is None:
            return fallback
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or fallback
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, list):
            if not value:
                return fallback
            return ', '.join(self._compact_values(value))
        return str(value).strip() or fallback

    def _count_text(self, value: Any, noun: str) -> str:
        if isinstance(value, list):
            count = len(value)
            return f'{count} {noun}'
        if value:
            return f'1 {noun}'
        return f'no {noun}'

    def _compact_values(self, values: Any) -> list[str]:
        items: list[str] = []
        if not values:
            return items
        for value in values:
            text = self._text(getattr(value, 'name', value), '')
            if text:
                items.append(text)
        return items[:4]

    def _to_sentence(self, value: Any) -> str:
        text = self._text(value, '')
        if not text:
            return 'Not disclosed'
        text = text.replace('_', ' ').strip()
        return text[:1].upper() + text[1:] if text else text

    def _shorten(self, value: str, limit: int) -> str:
        text = self._text(value, '')
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + '…'

    def _slugify(self, value: str) -> str:
        cleaned = ''.join(ch.lower() if ch.isalnum() else '_' for ch in value)
        while '__' in cleaned:
            cleaned = cleaned.replace('__', '_')
        return cleaned.strip('_') or 'company_intelligence_report'

    def _snapshot_text(self, value: Any, fallback: str) -> str:
        if isinstance(value, list):
            return f'{len(value)} items {fallback}'
        if value:
            return fallback
        return 'No signal available'

    def _stat_meaning(self, key: str) -> str:
        meanings = {
            'pages_crawled': 'Direct pages captured from the target site',
            'total_urls': 'All URL-like records in the evidence set',
            'internal_links': 'Unique internal crawl endpoints',
            'external_links': 'Unique public sources outside the site',
            'documents': 'PDF, DOC, PPT, or other document artifacts',
            'images': 'Image assets detected during crawl',
            'videos': 'Video assets detected during crawl',
            'sources_used': 'Combined discovery and crawl sources used by the report',
            'extraction_time_seconds': 'Operational timing placeholder for the current run',
            'ai_tokens_estimate': 'Approximate prompt size used during synthesis',
        }
        return meanings.get(key, 'Operational metadata')

    def _classify_source(self, url: str) -> str:
        lowered = (url or '').lower()
        if 'wikipedia.org' in lowered or 'crunchbase' in lowered:
            return 'Reference'
        if 'cars.com' in lowered or 'kbb.com' in lowered or 'kelley blue book' in lowered:
            return 'Market Research'
        if 'instagram.com' in lowered or 'youtube.com' in lowered or 'twitter.com' in lowered or 'x.com' in lowered or 'facebook.com' in lowered:
            return 'Social Media'
        if 'news' in lowered or 'press' in lowered:
            return 'News'
        if 'blog' in lowered:
            return 'Blog'
        if 'investor' in lowered or 'financial' in lowered:
            return 'Investor'
        if 'careers' in lowered or 'jobs' in lowered:
            return 'Careers'
        if 'docs' in lowered or 'developer' in lowered or 'api' in lowered:
            return 'Tech'
        return 'Web'

    def _financial_signal(self, graph: CompanyKnowledgeGraph, key: str) -> str:
        values = self._graph_values(graph, 'financials')
        if values:
            return values[0]
        return 'Not disclosed'

    def _graph_values(self, graph: CompanyKnowledgeGraph, field: str) -> list[str]:
        values = getattr(graph, field, []) or []
        return [self._text(item) for item in values if self._text(item)]

    def _financial_table_value(self, graph: CompanyKnowledgeGraph, key: str) -> str:
        values = self._graph_values(graph, 'financials')
        return values[0] if values else 'Not disclosed'

    def _mini_table_rows(self, values: list[str]) -> list[list[str]]:
        if not values:
            return [['No data', 'No data available']]
        return [[value, 'Public evidence'] for value in values[:6]]

    def _products_table(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[list[str]]:
        values = result.products or self._graph_values(graph, 'products')
        if not values:
            return [['No product names extracted', '']]
        return [[value, 'Product / service offering'] for value in values[:8]]

    def _maybe_value(self, value: Any) -> str:
        return self._text(value, 'Not disclosed')

    def _competitor_source(self, competitor: Any) -> str:
        return getattr(competitor, 'reason', '') or 'Public discovery'

    def _financial_signal_text(self, graph: CompanyKnowledgeGraph, fallback: str) -> str:
        values = self._graph_values(graph, 'financials')
        return values[0] if values else fallback

    def _lookup(self, graph: CompanyKnowledgeGraph, field: str) -> list[str]:
        return self._graph_values(graph, field)

    def _product_rows(self, result: CompanyResearchResult, graph: CompanyKnowledgeGraph) -> list[list[str]]:
        values = result.products or self._graph_values(graph, 'products')
        if not values:
            return [['No product signals found', '']]
        return [[self._shorten(value, 28), 'Product'] for value in values[:8]]

    def _build_reference_list(self, sources: list[ResearchSource], references: list[ResearchSource]) -> list[ResearchSource]:
        combined = list(references or []) + list(sources or [])
        seen: set[str] = set()
        ordered: list[ResearchSource] = []
        for item in combined:
            url = (item.url or '').strip().lower()
            if not url or url in seen:
                continue
            seen.add(url)
            ordered.append(item)
        return ordered
